import kivy
kivy.require('1.7.1')

from os.path import join, abspath, isdir, basename
from os import walk, chdir, getcwd, remove
from glob import glob
from kivy.atlas import Atlas

DEFAULT_SIZE = 64


def create(folder):
    cwd = getcwd()
    images = []
    for root, dirname, filenames in walk(folder):
        for filename in filenames:
            image = join(root, filename)[len(folder) + 1:]
            print image
            images.append(image)

    chdir(folder)
    outfn = None
    size = DEFAULT_SIZE
    while not outfn:
        try:
            fname = join('..', basename(folder))
            outfn=Atlas.create(fname, images, size, use_path=True)
        except:
            pass
        if not outfn or ((size<1024) and (len(outfn)>1 and len(outfn[1])>2)):
                numfiles = len(outfn[1]) if outfn else 0
                for i in range (0, numfiles):
                    outf = '%s-%d.png' % (fname, i)
                    try:
                        remove(outf)
                    except:
                        pass
                outfn = None
        size *= 2
    chdir(cwd)

def main(argv=None):
    try:
        create('screens')
        create('themes')

    except Exception, e:
        print e


if __name__ in ('__main__'):
    main()
