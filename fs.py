#!/usr/bin/env python

# yum install fusepy
# https://www.stavros.io/posts/python-fuse-filesystem/
# (LICENSED BSD)


import os
import errno
import stat
import shutil

VERBOSE = False
GET_DIR = [".", ".."]

from fuse import FUSE,FuseOSError, Operations, c_stat
class nostat(c_stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 2
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0
    def as_dict(self):
        return dict((key, getattr(self, key)) for key in ('st_atime',
                                                          'st_ctime',
                                                          'st_mtime',
                                                          'st_gid',
                                                          'st_mode',
                                                          'st_nlink',
                                                          'st_size',
                                                          'st_uid',
                                                          'st_ino'))


class CacheDir(Operations):
    def __init__(self, slow_dir, fast_dir, maxfilesize=3*1024*1024*1024, verbose=VERBOSE):
        self.slow_dir = slow_dir.rstrip("/")
        self.fast_dir = fast_dir.rstrip("/")
        self.maxfilesize = maxfilesize #default 3GB #stream everything else from slow disk
        self.verbose=verbose


    # Filesystem methods
    # ==================

    def access(self, path, mode):
        fast_path = "%s%s" %(self.fast_dir, path)
        if not os.access(fast_path,mode):
            raise FuseOSError(errno.EACCES)


    def getattr(self, path, fh=None):
        if self.verbose:
            print "get attr"
            print path
        base = nostat()
        if path == "/":
            base.st_mode = int(stat.S_IFDIR | 0755)
            base.st_nlink = 2
        else:
            fast_name = "%s%s" %(self.fast_dir, path)
            if self.verbose: print "checking:", fast_name
            if os.path.isfile(fast_name):
                st = os.lstat(fast_name)
                if self.verbose:
                    print "found:", fast_name

            else:
                slow_name = "%s%s" %(self.slow_dir, path)
                if self.verbose: print "checking:", slow_name
                if os.path.isfile(slow_name):
                    if self.verbose:
                        print "found:", slow_name, fast_name
                    st = os.lstat(slow_name)
                    if st.st_size > self.maxfilesize:
                        if self.verbose: print "symlinking:", slow_name, fast_name
                        os.symlink(slow_name, fast_name)
                    else:
                        if self.verbose: print "copying:", slow_name, fast_name
                        shutil.copy(slow_name, fast_name)
                        st = os.lstat(fast_name)

                elif os.path.isdir(slow_name):
                    st = os.lstat(slow_name)
                    try:
                        os.mkdir(fast_name, st.st_mode)
                    except OSError:
                        pass #try/catch more reliable than if not exists -> create
                else:
                    raise FuseOSError(errno.ENOENT)

            output = dict((key, getattr(st, key)) for key in ('st_atime',
                                                          'st_ctime',
                                                          'st_mtime',
                                                          'st_gid',
                                                          'st_mode',
                                                          'st_nlink',
                                                          'st_size',
                                                          'st_uid',
                                                          'st_ino'))
            if not stat.S_ISDIR(st.st_mode):
                output['st_mode'] = 41471
                output['st_size'] = 20
            if self.verbose: print output
            return output
        if self.verbose: print base.as_dict()
        return base.as_dict()


    def readlink(self, path):
        fast_dir = "%s%s" %(self.fast_dir, path)
        os.utime(fast_dir, None)
        if self.verbose:
            print "readlink"
            print path, fast_dir
        return fast_dir


    def release(self, path, fh):
        if self.verbose:
            print "release"
            print path
            print fh
        return os.close(fh)

    def readdir(self, path, fh):
        if self.verbose: print "readdir", path, fh
        return GET_DIR

def start_filesystem(mountpoint, fast_dir, slow_dir, verbose=VERBOSE):
    FUSE(CacheDir(slow_dir, fast_dir, verbose=verbose), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print "Usage: %s <mount point> <fast_dir> <slow_dir>" %sys.argv[0]
        exit(-1)
    start_filesystem(sys.argv[1], sys.argv[2], sys.argv[3])