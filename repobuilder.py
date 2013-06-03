# *
# *  Copyright (C) 2013 Paul Backhouse
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  Based on code by j48antialias:
# *  https://anarchintosh-projects.googlecode.com/files/addons_xml_generator.py
 
import os
import sys
import fnmatch
import shutil
import md5
from StringIO import StringIO
from lxml import etree
from zipfile import ZipFile
# Compatibility with 3.0, 3.1 and 3.2 not supporting u"" literals
if sys.version < '3':
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

def _save_file( data, file ):
    try:
        # write data to the file
        open( file, "w" ).write( data )
    except Exception, e:
        # oops
        print "An error occurred saving %s file!\n%s" % ( file, e, )


def generate_md5( filename ):
    # create a new md5 hash
    try:
        import md5
        m = md5.new( open( filename, "r" ).read() ).hexdigest()
    except ImportError:
        import hashlib
        m = hashlib.md5( open( filename, "r", encoding="UTF-8" ).read().encode( "UTF-8" ) ).hexdigest()
    return m

    try:
        _save_file( m.encode( "UTF-8" ), file="addons.xml.md5" )
    except Exception as e:
        print("An error occurred creating addons.xml.md5 file!\n%s" % e)

def get_addon_contents(filename):
    """
    Takes a filename and returns the contents of the file with
    initial <?xml...> element chomped out
    """
    lines = open( filename, "r" ).read().splitlines()
    for line in lines:
        line.rstrip()
        if ( line.find( "<?xml" ) >= 0 ):
            lines.remove(line)
    return u('\n').join(lines)

def filterdirectory(directory, filehandle):
    """
    Takes a directory and returns its contents
    as a list, filtered according to the contents
    of filehandle
    """
    contents = [os.path.normpath(os.path.join(directory, x)) for x in os.listdir(directory)]
    for line in filehandle:
        filtered = fnmatch.filter(contents, line.strip())
        contents = list(set(contents)-set(filtered))
    for x in contents:
        if os.path.isdir(x):
            filehandle.seek(0)
            contents.extend(filterdirectory(x,filehandle))
            contents.remove(x)
    return contents

if ( __name__ == "__main__" ):

    if not sys.argv[1:]:
        print "Usage: $repobuilder <directory1> <directory2>..."
        sys.exit(1)
    
    #we will want to comeback to the folder we executed the command from
    repofolder = os.path.realpath(os.curdir)
    #prepare download folder
    if not os.path.isdir('download'):
        os.mkdir('download')
    downloadfolder = os.path.realpath('download')
    
    #create empty addons file
    addons_xml = u("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n")

    for directory in sys.argv[1:]:
        #first some sanity checks
        if ( not os.path.isdir( directory )):
            print "'%s' is not a directory" % directory
            continue
        addon_xml = os.path.join( directory, "addon.xml" )
        if ( not os.path.isfile( addon_xml )):
            print "Couldn't find 'addon.xml' in directory '%s'" % directory
            continue
        icon =  os.path.join( directory, "icon.png" )
        if ( not os.path.isfile( icon )):
            print "Couldn't find 'icon.png' in directory '%s'" % directory
            continue
        try:
            tree = etree.parse(addon_xml)
        except:
            print "Could not parse addon.xml for %s" % directory
            continue

        #get some useful data from the xml tree
        root = tree.getroot()
        version = root.get('version')
        id = root.get('id')
        print "######################################"
        print "Addon '%s', version '%s'." % (id, version)
        print "######################################"
        #add addon into addons
        addon_contents = get_addon_contents(addon_xml)
        addons_xml += addon_contents.rstrip() + u("\n")

        #make folder to recieve zip file
        zipfolder = os.path.join(downloadfolder,id)
        if not os.path.isdir(zipfolder):
            os.mkdir(zipfolder)
        
        #build the list of files to zip
        os.chdir(directory)
        try:
            pattern = open('exclude.lst', 'r')
        except:
            pattern = StringIO()

        ziplist = filterdirectory(os.curdir,pattern)
        print "Building zip file..."
        with ZipFile(os.path.join(zipfolder,id+'-'+version+'.zip'), 'w') as zippy:
            for entry in ziplist:
                print "Adding %s ..." % entry
                zippy.write(entry, os.path.join(id,entry))
        
        #copy the icon
        shutil.copy(icon, zipfolder)
        os.chdir(repofolder)
    #finish up with addons
    print "Creating addons.xml..."
    addons_xml = addons_xml.strip() + u("\n</addons>\n")
    _save_file( addons_xml.encode( "UTF-8" ), file="addons.xml" )
    #generate md5
    print "Creating addons.xml.md5..."
    m = md5.new( open( "addons.xml" ).read() ).hexdigest()
    _save_file( m, file="addons.xml.md5" )
    print "Done!"