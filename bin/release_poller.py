#!/usr/bin/env python
import logging

import os
from os import path
import shutil
import datetime

import subprocess
import getpass

import json

import urllib
import httplib

from collections import namedtuple

import re
import logging

default_repository = "/lab/gos/RosettaCommons/main.git"
default_deployment_directory = "/work/buildbot/builds/release"
default_branch_prefix = "weekly_releases"
default_buildmaster = "buildbot0:8010"
default_release_weeks = 4

default_track_changes = "relase_poller.state.json"

BranchInfo = namedtuple("BranchInfo", ["name", "datetime", "revision"])

def listdir_nolinks(dirpath):
    return [d for d in os.listdir(dirpath) if not path.islink(path.join(dirpath, d))]

def get_deployed_branches(deployment_directory, branch_prefix):
    prefixed_deployment_dir = path.join(deployment_directory, branch_prefix)
    if not path.exists(prefixed_deployment_dir):
        return []

    branches = listdir_nolinks(prefixed_deployment_dir)

    deployed_branches = []

    for b in branches:
        full_name = "/".join((branch_prefix, b))
        deployed_revisions = listdir_nolinks(path.join(deployment_directory, branch_prefix, b))

        assert len(deployed_revisions) == 1
        deployed_revision = deployed_revisions[0]

        deployed_date = datetime.datetime.fromtimestamp(path.getmtime(path.join(deployment_directory, branch_prefix, b, deployed_revision)))

        deployed_branches.append(BranchInfo(full_name, deployed_date, deployed_revision))

    logging.info("Deployed branches:\n%s", "\n".join(str(b) for b in deployed_branches))
    return deployed_branches

def get_branch_data(repository, branch_names):
    if isinstance(branch_names, basestring):
        unpack = True
        branch_names = [branch_names]
    else:
        unpack = False

    branch_times = [datetime.datetime.fromtimestamp(int(l.strip())) for l in  subprocess.check_output(
        ["git", "show", "-s", "--format=%ct"] + list(branch_names), cwd=repository).splitlines()]

    branch_revisions = [l.strip() for l in subprocess.check_output(
        ["git", "show", "-s", "--format=%H"] + list(branch_names), cwd=repository).splitlines()]

    result = [BranchInfo(*i) for i in zip(branch_names, branch_times, branch_revisions)]

    return result if not unpack else result[0]

def get_release_branches(repository, branch_prefix):
    branch_names = [l[2:] for l in subprocess.check_output(["git", "branch"], cwd=repository).splitlines()]
    branch_names = [b for b in branch_names if b.find("management") == -1 and b.split("/")[0] == branch_prefix]

    branches = get_branch_data(repository, branch_names)

    logging.info("Release branches:\n%s", "\n".join(str(b) for b in branches))
    return branches

def get_root_info(repository, root_branch_name, target_branch_info):
    merge_base_revision = subprocess.check_output(
            ["git", "merge-base", root_branch_name, target_branch_info.name], cwd=repository).strip()
    merge_base_time = datetime.datetime.fromtimestamp(int(subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", merge_base_revision], cwd=repository).strip()))

    merge_base_info = BranchInfo(target_branch_info.name, merge_base_time, merge_base_revision)

    return merge_base_info

def resolve_unbuilt_branches(repository, deployment_directory, branch_prefix, timelimit):
    now = datetime.datetime.now()

    deployed_branches = get_deployed_branches(deployment_directory, branch_prefix)
    deployed_set = set((b.name, b.revision) for b in deployed_branches)

    released_branches = get_release_branches(repository, branch_prefix)
    candidate_releases = [b for b in released_branches if now - b.datetime < timelimit]
    logging.info("Candidate releases:\n%s", "\n".join(str(b) for b in candidate_releases))

    release_targets = [get_root_info(repository, "master", c) for c in candidate_releases]
    logging.info("Release merge roots:\n%s", "\n".join(str(b) for b in release_targets))

    return [t for t in release_targets if not (t.name, t.revision) in deployed_set]


def resolve_origin_url(repository):
    remote_data = [l.strip().split() for l in subprocess.check_output(["git", "remote", "-v", "show"], cwd=repository).splitlines()]

    origin = [d for d in remote_data if d[0] == "origin" and d[2] == "(fetch)"]
    assert len(origin) == 1
    url = origin[0][1]

    if url.find("@") != -1 and not url.startswith("ssh://"):
        url = "ssh://" + url

    return url

def submit_branch_changes(buildmaster, repository, target_branch):
    source_repo_url = resolve_origin_url(repository)
    author = getpass.getuser()
    hook_path = "/change_hook/base"

    conn = httplib.HTTPConnection(buildmaster)
    try:
        logging.info("Submitting branch: %s", target_branch)

        change_data = dict(
                repository = source_repo_url,

                category = "release",

                branch = target_branch.name,
                revision = target_branch.revision,
                project = "",

                comments = "Release %s (merge base %s %s)" % (target_branch.name, "master", target_branch.name),
                author = author)
        logging.info("Branch change data: %s", change_data)

        params = urllib.urlencode(change_data)
        headers = {
                "Content-type": "application/x-www-form-urlencoded",
                 "Accept": "text/plain"}

        logging.info("Request host: %s path: %s", buildmaster, hook_path)
        logging.info("Request header: %s", headers)
        logging.info("Request params: %s", params)
        conn.request("POST", hook_path, params, headers)
        response = conn.getresponse()
        data = response.read()

        logging.info("Request response: %s", response)
        logging.info("Request data: %s", data)

        if not response.status is 202:
            logging.error("Branch %s submission failed, request status: %s", t, response.status)
            raise ValueError("Branch %s submission failed, request status: %s data: %s" % target_branch, response.status, data)
    finally:
        conn.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

    import argparse

    parser = argparse.ArgumentParser(description="Scan for release branches in RosettaCommons repo and issue buildbot build requests.")

    parser.add_argument("--repository", default=default_repository)
    parser.add_argument("--deployment_directory", default=default_deployment_directory)
    parser.add_argument("--branch_prefix", default=default_branch_prefix)
    parser.add_argument("--buildmaster", default=default_buildmaster)
    parser.add_argument("--release_weeks", type=int, default=default_release_weeks)
    parser.add_argument("--track_changes", default=default_track_changes)
    parser.add_argument("--dry_run", action="store_true", default=False)
    args = parser.parse_args()

    change_targets = resolve_unbuilt_branches(args.repository, args.deployment_directory, args.branch_prefix, datetime.timedelta(weeks = args.release_weeks) )

    if args.track_changes and path.exists(args.track_changes):
        poller_state = json.load(open(args.track_changes))
    else:
        poller_state = dict(submitted_changes = [])

    logging.info("Loaded poller state:\n%s", poller_state)

    for t in change_targets:
        if [t.name, t.revision] in poller_state["submitted_changes"]:
            logging.info("Skipping submitted change: %s", t)
        else:
            if not args.dry_run:
                submit_branch_changes(args.buildmaster, args.repository, t)
            poller_state["submitted_changes"].append([t.name, t.revision])

    if not args.dry_run:
        with open(args.track_changes, "w") as state:
            json.dump(poller_state, state, indent=4)
