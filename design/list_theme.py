import kivy
kivy.require('1.7.1')

from os import getcwd
from os.path import basename
from glob import glob
from kivy.atlas import Atlas

def main(argv=None):
    try:
        cwd = getcwd()
        for path in glob('*.atlas'):
            a = Atlas(path)
            print 'Atlas %s:' % basename(path)
            for key in a.textures.keys():
                print '\t', key

    except Exception, e:
        print e


if __name__ in ('__main__'):
    main()
