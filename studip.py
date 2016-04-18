import errno, json, subprocess
from http.client import HTTPSConnection
from base64 import b64encode
from os import path, makedirs, devnull
from shutil import unpack_archive, get_unpack_formats, register_unpack_format
from getpass import getpass



APIBASE = 'studip.uos.de'
APIPATH = '/plugins.php/restipplugin/api/%s';



def printjson(data):
  print(jsonh.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))



def mkdir_p(dir):
  """Recursivly creates directories if they do not already exist."""
  try:
    makedirs(dir)
  except OSError as exc:
    if exc.errno == errno.EEXIST and path.isdir(dir): pass
    else: raise



def try_cmd(cmd):
  """Checks if a specific command is available on system level."""
  try:
    subprocess.call(cmd, stdout=open(devnull, 'wb'))
  except OSError as e:
    if e.errno == errno.ENOENT: return False
    else: raise
  return True



def unrar(src, dst):
  """Wrapper for the unrar system tool."""
  if dst[-1] != '/': dst = dst + '/' # Enforce trailing slash.
  subprocess.call(['unrar', '-inul', '-f', 'x', src, dst])



def un7z(src, dst):
  """Wrapper for the 7z system tool."""
  subprocess.call(
    ['7z', 'x', '-y', '-o' + dst, src],
    stdout=open(devnull, 'wb')
  )



def download(url, filename, name, dir):
  """Function for easily downloading a file and possibly unpacking it.

  Keyword arguments:
  url
  filename -- Target filename.
  name -- Name for the resulting folder when unpacked.
  dir -- Target directory.
  """
  response = get(url)
  with open(dir + filename, 'wb') as file:
    file.write(response.read())
    while not response.closed:
      chunk = response.read(200)
      if not chunk: break
      file.write(chunk)

  ext = path.splitext(filename)[-1].lower();
  if ext in download.unpack_formats:
    src = path.join(dir, filename)
    dst = path.join(dir,  path.splitext(name)[0])
    unpack_archive(src, dst)

download.unpack_formats = list()



def fetch(courseId, folderId = '', dir = 'download', force = True):
  """Fetch all files for a specific course and (optionally) folder.

  Keyword arguments:
  courseId -- StudIP course ID
  folderId -- StudIP folder ID
  dir -- Target folder to write downloaded files to. (default: `download`)
  force -- Overwrite existing files. (default: false)
  """
  if folderId != '': folderId = '/' + folderId
  url = APIPATH % 'documents/' + courseId + '/folder' + folderId
  data = get(url)

  mkdir_p(dir)
  dir = dir + '/'
  print(dir)

  # Fetch documents.
  documenturl = APIPATH % 'documents/%s/download'
  for document in data['documents']:
    if not path.isfile(dir + document['filename']) or force:
      print(document['filename'])
      download(documenturl % document['document_id'],
               document['filename'], document['name'], dir)

  # Fetch subfolders.
  for folder in data['folders']:
    fetch(courseId, '/' + folder['folder_id'], dir + folder['name'], force)



def get(path = None, headers = None):
  """Wrapper for easy HTTPS get requests."""
  if get.conn is None:
    # Initialize the HTTPS connection required for all future requests.
    get.conn = HTTPSConnection(APIBASE)
  if headers is not None:
    # Set required request headers, for example for authentication.
    get.headers = headers
  if path is not None:
    # Execute the actual get request and handle the response.
    get.conn.request('GET', path, headers = get.headers)
    res = get.conn.getresponse()
    if res.getheader('content-type').split(';')[0] == 'application/json':
      return json.loads(res.read().decode('utf-8'))
    return res

get.conn = None
get.headers = None



def main():
  # Read auth data from stdin.
  username = input('Username: ')
  password = getpass()
  auth = b64encode(bytes(username + ':' + password, 'utf-8')).decode('ascii');
  get(headers = { 'Authorization' : 'Basic %s' %  auth })

  # User can either enter a courseId or choose through the CLI.
  courseId = input('Course id? Otherwise just press enter. --> ')
  if (len(courseId) > 0):
    url = APIPATH % 'courses/' + courseId
    course = get(url)['course']
  else:
    # Let user choose a semester.
    url = APIPATH % 'courses/semester';
    semesters = get(url)['semesters']
    for idx in range(0, len(semesters)):
      print(idx, semesters[idx]['title'])

    # Let user choose a course from that semester.
    semesterId = semesters[int(input('semester index: '))]['semester_id']
    url = APIPATH % 'courses/semester/' + semesterId;
    courses = get(url)['courses']
    for idx in range(0, len(courses)):
      print(idx, courses[idx]['title'])

    # Fetch the files from this course..
    course = courses[int(input('course index: '))]

  # Overwrite existing files?
  force = False
  shouldforce = input('Overwrite existing files (if any)? [y], [n] ')
  if shouldforce in ['Y', 'y', 'yes', 'TRUE', 'true', '1']:
    force = True

  fetch(course['course_id'], '', course['title'], force)




def init_additional_unpackers():
  """Add external libraries for unpacking files.

  Checks if `7z` or `unrar` are installed on the host system.
  """
  if try_cmd('7z'):
    register_unpack_format('7zip', [
      '.zipx', '.gz', '.z', '.cab',
      '.rar', '.lzh', '.7z', '.xz'
    ], un7z)
  elif try_cmd('unrar'):
    register_unpack_format('unrar', ['.rar'], unrar)

  formats = get_unpack_formats()
  formats = list(map(lambda item: item[1], formats))
  formats = [item for sublist in formats for item in sublist]
  download.unpack_formats = formats



if __name__ == '__main__':
  init_additional_unpackers()
  main()
