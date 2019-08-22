# =============================================================================
# codePost – Blackboard Utility
#
# Takes submissions downloaded from Blackboard and transforms the file
# structure into a structure that codePost will recognize.
#
# =============================================================================

# Python stdlib imports
import os
import argparse
import csv
import shutil
import re

# =============================================================================

parser = argparse.ArgumentParser(description='Blackboard to codePost!')
parser.add_argument(
    'submissions', help='The directory of submissions downloaded from Blackboard')
parser.add_argument(
    'roster', help='The course roster of students that includes first name, last name, and email')
parser.add_argument('-s', '--simulate', action='store_true')
args = parser.parse_args()

# =============================================================================
# Constants

OUTPUT_DIRECTORY = 'codepost_upload'
ERROR_DIRECTORY = 'errors'

_cwd = os.getcwd()
_upload_dir = os.path.join(_cwd, OUTPUT_DIRECTORY)
_error_dir = os.path.join(_cwd, ERROR_DIRECTORY)

# =============================================================================
# Helpers


def normalize(string):
  return string.lower().strip()


def delete_directory(path):
  if os.path.exists(path):
    shutil.rmtree(path)


def validate_csv(row):
  for key in row.keys():
    if 'blackboard' in normalize(key):
      blackboard_id = key
    elif 'email' in normalize(key):
      email = key

  if blackboard_id == None or email == None:
    if blackboard_id == None:
      print("Missing header: blackboard_id")
    if email == None:
      print("Missing header: email")

    raise RuntimeError(
        "Malformatted roster. Please fix the headers and try again.")

    return (blackboard_id, email)
  else:
    return (blackboard_id, email)


def blackboard_id_to_email(roster):
  with open(roster, mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    blackboard_id, email = (None, None)
    blackboard_id_to_email = {}
    for row in csv_reader:
      if line_count == 0:
        (blackboard_id, email) = validate_csv(row)
        line_count += 1

      # Blackboard convention: map {blackboard_id} to {codePost email}
      blackboard_id_to_email[
          normalize(row[blackboard_id])] = normalize(row[email])
      line_count += 1
    return blackboard_id_to_email


def check_for_partners(file_name):
  filepath = os.path.join(args.submissions, file_name)
  emails = [line.rstrip('\n') for line in open(filepath, 'r')]
  EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"
  filtered_emails = [x for x in emails if re.match(EMAIL_REGEX, x)]

  return filtered_emails

# =============================================================================

if (args.simulate):
  print('\n~~~~~~~~~~~ START SIMULATION ~~~~~~~~~~~')

print('\nSetting up directories...')

# Overwrite the directories if they exist already
if not args.simulate:
  delete_directory(_upload_dir)
  delete_directory(_error_dir)

  os.makedirs(_upload_dir)
  os.makedirs(_error_dir)

print('\t/{}'.format(OUTPUT_DIRECTORY))
print('\t/{}'.format(ERROR_DIRECTORY))

print('\nReading and validating roster...')
blackboard_id_to_email = blackboard_id_to_email(args.roster)
print('\tVALID')

print('\nChecking submissions for partners...')

files = os.listdir(args.submissions)
folders = []
for file in files:
  file_name = file.split('_')[-1]
  if 'partners' in file_name:
    partners = check_for_partners(file)
    folders.append(partners)

print('\t{}'.format(folders))

print('\nCreating student folders...')
for student in blackboard_id_to_email:
  found = False
  for folder in folders:
    if blackboard_id_to_email[student] in folder:
      found = True
      break

  if not found:
    folders.append([blackboard_id_to_email[student]])

for folder in folders:
  folder_name = ",".join(folder)
  if not args.simulate:
    os.makedirs(os.path.join(_upload_dir, folder_name))
  print('\t{}'.format(folder_name))


print('\nMapping and copying files...')
for file in files:
  blackboard_id = file.split('_')[1]
  file_name = file.split('_')[-1]

  if normalize(blackboard_id) in blackboard_id_to_email:
    email = blackboard_id_to_email[blackboard_id]
    found = False

    for folder in folders:
      if email in folder:
        folder_name = ",".join(folder)
        found = True
        if not args.simulate:
          shutil.copyfile(os.path.join(args.submissions, file), os.path.join(
              os.path.join(_upload_dir, folder_name), file_name))
        print('\t{}'.format(os.path.join(
            os.path.join(_upload_dir, folder_name), file_name)))

    if not found:
      if not args.simulate:
        shutil.copyfile(os.path.join(args.submissions, file),
                        os.path.join(_error_dir, file))
      print('\tERROR: {}'.format(os.path.join(_error_dir, file)))
  else:
    if not args.simulate:
      shutil.copyfile(os.path.join(args.submissions, file),
                      os.path.join(_error_dir, file))
    print('\tERROR: {}'.format(os.path.join(_error_dir, file)))

if args.simulate:
  print('\n~~~~~~~~~~~ END SIMULATION ~~~~~~~~~~~\n')
