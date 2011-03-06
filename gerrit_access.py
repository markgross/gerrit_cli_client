#! /usr/bin/python

#
# python wrapper for parsing the return values from :
# ssh -p 29418 android.example.com  gerrit query --format TEXT --current-patch-set 'status:open is:starred'
#

import subprocess, shlex

root = "change I"
change_keywords = ["  project: " ,"  branch: " ,"  id: " , "  number: " ,
"  subject: " ,"  owner:", "  url: " , "  lastUpdated: " ,"  sortKey: " ,
"  open: " , "  status: ", "  currentPatchSet:"] 
patchset_keywords = ["    number: ", "    revision: ", "    ref: ", "    uploader:", "    approvals:"]
approvals_keywords = [ "      type: " ,"      description: " , "      value: " ,
        "      grantedOn: ", "      by:"]


cmd = ['repo', 'forall', '.', '-c', 'echo $REPO_PROJECT']
P = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
REPO_PROJECT = P.communicate()[0]
cmd = ['repo', 'forall', '.', '-c', 'echo $REPO_RREV']
P = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
REPO_RREV = P.communicate()[0]



class developer:
    def __init__(self, lines):
        self.name = lines[0][2+lines[0].find(": "):]
        self.email = lines[1][2+lines[1].find(": "):]

class approval:
    def __init__(self, lines):
        i = 0
        for l in lines:
            i += 1
            if 0 == l.find( approvals_keywords[0]):
                self.Type = l[2+l.find(": "):]
                continue
            if 0 == l.find( approvals_keywords[1]):
                self.description = l[2+l.find(": "):]
                continue
            if 0 == l.find( approvals_keywords[2]):
                self.value = l[2+l.find(": "):]
                continue
            if 0 == l.find( approvals_keywords[3]):
                self.grantedOn = l[2+l.find(": "):]
                continue
            if 0 == l.find( approvals_keywords[4]):
                self.by = developer(lines[i:i+2])
                break

def approvals(lines):
    ret = []
    for i in xrange(len(lines)):
        if 0 == lines[i].find( approvals_keywords[0]):
            ret.append(approval(lines[i:i+7]))

    return ret

class patchSet:
    def __init__(self, lines):
        i = 0
        for l in lines:
            i += 1
            if 0 == l.find( patchset_keywords[0]):
                self.number = l[2+l.find(": "):]
                continue
            if 0 == l.find( patchset_keywords[1]):
                self.revision = l[2+l.find(": "):]
                continue
            if 0 == l.find( patchset_keywords[2]):
                self.ref = l[2+l.find(": "):]
                continue
            if 0 == l.find( patchset_keywords[3]):
                self.uploader = developer(lines[i:i+2])
                continue
            if 0 == l.find( patchset_keywords[4]):
                self.approvals = approvals(lines[i:])
                break


class Change:
    def __init__(self, lines):
        i = 0
        for l in lines:
            i += 1 
            if 0 == l.find( change_keywords[0]):
                self.project = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[1]):
                self.branch = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[2]):
                self.id = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[3]):
                self.number = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[4]):
                self.subject = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[5]):
                self.owner = developer(lines[i:i+2])
                continue
            if 0 == l.find( change_keywords[6]):
                self.url = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[7]):
                self.lastUpdated = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[8]):
                self.sortKey = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[9]):
                self.Open = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[10]):
                self.status = l[2+l.find(": "):]
                continue
            if 0 == l.find( change_keywords[11]):
                self.currentPatchSet = patchSet(lines[i:])
                break

    def fetch(self):
        """git fetch ssh://mgross@android.intel.com:29418/a/bsp/hardware/intel/libcamera refs/changes/16/4816/1"""
        #assume CWD is correct.  
        git_cmd = ["git", "fetch", "ssh://mgross@android.intel.com:29418/"+self.project, self.currentPatchSet.ref]
        ret = subprocess.call(git_cmd)
        print self.url
        return ret

    def make_patch(self):
        git_cmd = ["git", "format-patch", "-1", "FETCH_HEAD"]
        ret = subprocess.call(git_cmd)
        return ret

    def cherry_pick(self):
        git_cmd = ["git", "cherry-pick", "FETCH_HEAD"]
        ret = subprocess.call(git_cmd)
        return ret


def dumb_buff_to_struct(lines):
    """one pass parser of query output spit into lines"""
    changes = []
    start = 0
    Next = 0
    i = 0
    for l in lines:
        i += 1
        if root == l[:len(root)]:
            start = Next
            Next = i
            if Next > start + len(change_keywords):
                changes.append(Change(lines[start:Next]))
    
    changes.append(Change(lines[Next:]))

    return changes

def get_open_changes():
    """get changes that have + 1 or +2 approval marked by the uploader"""
    cmd = shlex.split(" ssh -p 29418 android.intel.com  gerrit query --format TEXT --current-patch-set 'status:open '")
    cmd[-1] = cmd[-1] + " project:" + REPO_PROJECT + " branch:" + REPO_RREV
    P = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
    out = P.communicate()
    if P.returncode == 0:
        lines = out[0].split('\n')
        #print lines
        changes = dumb_buff_to_struct(lines)
    return changes

def get_starred_changes():
    cmd = shlex.split(" ssh -p 29418 android.intel.com  gerrit query --format TEXT --current-patch-set 'status:open is:starred'")
    cmd[-1] = cmd[-1] + " project:" + REPO_PROJECT + " branch:" + REPO_RREV
    P = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
    out = P.communicate()
    if P.returncode == 0:
        lines = out[0].split('\n')
        #print lines
        changes = dumb_buff_to_struct(lines)
    return changes

def get_patches():
    changes = get_starred_changes()
    for c in changes:
        c.fetch()
        c.make_patch()

def list_ready_patches():
    """list changes that are marked by uploader as good"""
    changes = get_open_changes()
    for c in changes:
        try:
            for a in c.currentPatchSet.approvals:
                if a.Type == 'CRVW':
                    if c.currentPatchSet.uploader.name == a.by.name:
                        if a.value == "1" or a.value == '2':
                            print c.url
                            break
        except AttributeError:
            continue

def get_ready_patches():
    """get patches for changes that are marked by uploader as good"""
    changes = get_open_changes()
    for c in changes:
        try:
            for a in c.currentPatchSet.approvals:
                if a.Type == 'CRVW':
                    if c.currentPatchSet.uploader.name == a.by.name:
                        if a.value == "1" or a.value == '2':
                            c.fetch()
                            c.make_patch()
                            break
        except AttributeError:
            continue

def test():
    #get_patches()
    #get_ready_patches()
    list_ready_patches()

if __name__ == "__main__":
    test()

