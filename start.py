#!/usr/bin/env python


# https://www.stavros.io/posts/python-fuse-filesystem/
# (LICENSED BSD)


import os
import errno
import stat
import shutil

VERBOSE = False

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


class Passthrough(Operations):
    def __init__(self, slow_dir, fast_dir):
        self.slow_dir = slow_dir.rstrip("/")
        self.fast_dir = fast_dir.rstrip("/")

    # Helpers
    # =======



    # Filesystem methods
    # ==================

    def access(self, path, mode):
        fast_path = "%s%s" %(self.fast_dir, path)
        if not os.access(fast_path,mode):
            raise FuseOSError(errno.EACCES)


    def getattr(self, path, fh=None):
        if VERBOSE:
            print "get attr"
            print path
        base = nostat()
        if path == "/":
            base.st_mode = int(stat.S_IFDIR | 0755)
            base.st_nlink = 2
        else:
            fast_name = "%s%s" %(self.fast_dir, path)
            if VERBOSE: print "checking:", fast_name
            if os.path.isfile(fast_name):
                st = os.lstat(fast_name)
                if VERBOSE:
                    print "found:", fast_name

            else:
                slow_name = "%s%s" %(self.slow_dir, path)
                if VERBOSE: print "checking:", slow_name
                if os.path.isfile(slow_name):
                    if VERBOSE:
                        print "found:", slow_name, fast_name
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
            if VERBOSE: print output
            return output
        if VERBOSE: print base.as_dict()
        return base.as_dict()


    def readlink(self, path):
        fast_dir = "%s%s" %(self.fast_dir, path)
        os.utime(fast_dir, None)
        if VERBOSE:
            print "readlink"
            print path, fast_dir
        return fast_dir


    def release(self, path, fh):
        if VERBOSE:
            print "release"
            print path
            print fh
        return os.close(fh)

    def readdir(self, path, fh):
        '''This method is called when you list a directory.
           I.e. by calling ls /my_filesystem/
           The method getattr is called first, to see if path exists and is a directory.
           Returns a list of strings with the file or directory names in the directory *path*.'''
        if VERBOSE:
            print "readdir", path, fh
        file_objects = [".", "..", "my_file"]
        return file_objects

def main(mountpoint, fast_dir, slow_dir):
    FUSE(Passthrough(slow_dir, fast_dir), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print "Usage: %s <mount point> <fast_dir> <slow_dir>" %sys.argv[0]
        exit(-1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])