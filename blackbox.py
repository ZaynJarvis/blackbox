import os, errno, time, datetime, random, sys, stat, string

import requests
import urllib
import traceback
import keyring
import getpass
import logging
from pprint import pprint

from tqdm import tqdm
from lxml.html import fromstring
from urllib.parse import urlparse, unquote

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base

if sys.platform == 'win32':
    engine = create_engine('sqlite:///blackbox.db')
else:
    engine = create_engine('sqlite:///' + os.path.join(os.getcwd(),'blackbox.db'))

Base = declarative_base()

class File(Base):

    __tablename__ = "file"

    file_id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    file_url = Column(String, default=None, index=True)
    file_actual_url = Column(String, default=None, index=True)
    file_name = Column(String, default=None, index=True)
    file_actual_name = Column(String, default=None, index=True)

    file_downloaded = Column(Boolean, default=False, index=True)

    folder_path = Column(String, default=None, index=True)
    folder_url = Column(String, default=None, index=True)

    status = Column(String, default=None, index=True)
    remarks = Column(String, default=None, index=True)

    last_update_utc = Column(DateTime, default=datetime.datetime.utcnow(), index=True)
    last_update_local = Column(DateTime, default=datetime.datetime.now(), index=True)

    def __init__(self, folder_path, file_url, file_name):

        self.folder_path = folder_path
        self.file_url = file_url
        self.file_name = file_name

class Folder(Base):

    __tablename__ = "folder"

    folder_id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    folder_path = Column(String, default=None, index=True)
    folder_url = Column(String, default=None, index=True)

    files_extracted = Column(Boolean, default=False, index=True)
    subfolders_extracted = Column(Boolean, default=False, index=True)
    mother_coursemenu_extracted = Column(Boolean, default=False, index=True)
    is_mother_link = Column(Boolean, default=False, index=True)

    status = Column(String, default=None, index=True)
    remarks = Column(String, default=None, index=True)

    last_update_utc = Column(DateTime, default=datetime.datetime.utcnow(), index=True)
    last_update_local = Column(DateTime, default=datetime.datetime.now(), index=True)

    def __init__(self, folder_path, folder_url, is_mother_link):

        self.folder_path = folder_path
        self.folder_url = folder_url
        self.is_mother_link = is_mother_link

# Create Tables
Base.metadata.create_all(engine)

# Other Variables
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

legal_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
illegal_chars = '\/*?":|<>' # FYI only

blacklisted_file_extensions = ['asf', 'avi', 'mov', 'moov', 'mpg', 'mpeg', 'qt', 'swa', 'swf', 'wmv', 'flv', 'mp4', 'mpeg', 'movie']

def create_dir(full_file_path):
    print("create_dir(%s)" % full_file_path)

    full_path = os.path.join(full_file_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)

def intialize_db():

    global db_session

    if sys.platform == 'win32':
        engine = create_engine('sqlite:///blackbox.db')
    else:
        engine = create_engine('sqlite:///' + os.path.join(os.getcwd(),'blackbox.db'))

    Session = sessionmaker(bind=engine)
    db_session = Session()

    print("\n")
    print("Blackbox Database initialized!")

def get_title(response):
    try:
        return fromstring(response.content).findtext('.//title').decode('utf-8')
    except:
        return "<No Title Found>"

def clean_string(this_string):
    return ''.join(c if c in legal_chars else '_' for c in this_string)

def print_progress(response):
    print("\n")
    print("Title: " + get_title(response))
    # print("Status Code: " + str(response.status_code))
    # print("Response URL: " + response.url)

def download_file(url, response):

    print("\n")

    filename = unquote(url.split("/")[-1])
    print("Downloading %s ..." % filename)

    with open(filename, "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)

    print("Download complete for %s!" % filename)

def login():
    '''
    HTTP POST
    '''
    global requests_session, data_credentials

    login_url = "https://ntulearn.ntu.edu.sg/webapps/login/"
    # note that in email have encoded '@' like uuuuuuu%40gmail.com

    response = requests_session.post(login_url, headers=headers, data=data_credentials)
    print_progress(response)

def navigate(this_url, print_results=False, download=False, print_all_links=False, print_container_links_only=False): # , print_coursemenu_links_only=False):
    '''
    HTTP GET
    '''
    global requests_session

    response = requests_session.get(this_url, timeout=(15,15))

    if print_results:
        print_progress(response)
    if download:
        download_file(response.url, response)
    if print_all_links:
        pprint(fromstring(response.content).xpath('//a/@href'))
    if print_container_links_only:
        pprint(fromstring(response.content).xpath('//div[@id ="containerdiv"]//a/@href'))
    # if print_coursemenu_links_only:
    #     collection = fromstring(response.content).xpath('//ul[@id ="courseMenuPalette_contents"]//a')
    #
    #     link_collection = fromstring(response.content).xpath('//ul[@id ="courseMenuPalette_contents"]//a/@href')
    #     pprint(link_collection)
    #
    #     text_collection = []
    #     for child in collection:
    #         text_collection.append(child.text_content())
    #     pprint(text_collection)

def selenium_get_courses():

    global username, password

    CHROMEDRIVER_PATH = os.getcwd()

    BLACKBOARD_DOWNLOAD_PATH = os.path.join(CHROMEDRIVER_PATH, 'Downloads')

    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory': BLACKBOARD_DOWNLOAD_PATH,
             'download.prompt_for_download': False,
             'plugins.always_open_pdf_externally': True, }
    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.add_argument("--headless")

    if sys.platform == "win32":
        driver = webdriver.Chrome(os.path.join(CHROMEDRIVER_PATH, "boxdriver.exe"), options=chrome_options)
    else:
        os.chmod(os.path.join(CHROMEDRIVER_PATH, "boxdriver"), stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
        driver = webdriver.Chrome(os.path.join(CHROMEDRIVER_PATH, "boxdriver"), options=chrome_options)

    driver.get("https://ntulearn.ntu.edu.sg/webapps/login/")
    wait()


    email_field = driver.find_element_by_id("user_id")
    print(email_field)
    email_field.clear()
    email_field.send_keys(username)

    password_field = driver.find_element_by_id("password")
    password_field.clear()
    password_field.send_keys(password)

    try:
        email_field.send_keys(Keys.RETURN)
    except:
        driver_wait = WebDriverWait(driver, 10)
        home_page = driver_wait.until(EC.url_to_be("https://ntulearn.ntu.edu.sg/webapps/portal/execute/tabs/tabAction"))

    driver.get("https://ntulearn.ntu.edu.sg/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_13_1")
    wait()


    element = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, "coursefakeclass")))

    courses = driver.find_element_by_class_name("coursefakeclass").find_elements_by_tag_name("li")

    course_title_list = []
    course_url_list = []

    for course in courses:
        course_title_list.append(clean_string(course.find_element_by_tag_name('a').text))
        course_url_list.append(course.find_element_by_tag_name('a').get_attribute("href"))

    # pprint(course_title_list)
    # pprint(course_url_list) # for debug only

    return course_title_list, course_url_list

def commit_to_db_folder(course_title_list, course_url_list, parent_folder=None):
    for course in range(len(course_title_list)):

        if parent_folder == None:

            folder = save_to_db(Folder, folder_path = clean_string(course_title_list[course]), folder_url = course_url_list[course], is_mother_link = True)

        else:
            folder_path = parent_folder + r'\\' + clean_string(course_title_list[course])
            folder = save_to_db(Folder, folder_path=folder_path, folder_url=course_url_list[course], is_mother_link = False)
    print("Insertion into DB Folder completed.")

def clean_file_name(this_string):

    return clean_string('.'.join(this_string.split('.')[:-1])) + '.' + this_string.split('.')[-1]

def commit_to_db_file(file_title_list, file_url_list, folder_path):
    for course in range(len(file_title_list)):

        print("\n==================")
        print("FILE NAME IS: %s" % file_title_list[course])
        print("==================\n")

        file = save_to_db(File, folder_path = folder_path, file_name = file_title_list[course], file_url = file_url_list[course])

    print("Insertion into DB File completed.")

def save_to_db(table, **kwargs):
    '''
    folder = get_or_create(Folder, folder_path = 'abc', folder_url = 'def')
    :param table: Class object in sqlite
    :param kwargs: All arguments
    :return:
    '''

    global db_session

    instance = db_session.query(table).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = table(**kwargs)
        db_session.add(instance)
        db_session.commit()
        return instance

# ============================================================================================
# MOTHER COURSEMENU FUNCTIONS
# ============================================================================================

def get_coursemenu_text_and_links_from_mother_links(this_url, this_folder, print_results=False, print_coursemenu_links=False, add_to_folders=False):
    '''
    HTTP GET
    '''
    global requests_session

    # print("Running get_coursemenu_text_and_links_from_mother_links")
    # print(this_url)

    response = requests_session.get(this_url, timeout=(15,15))

    if print_results:
        print_progress(response)

    collection = fromstring(response.content).xpath('//ul[@id ="courseMenuPalette_contents"]//a')

    link_collection = fromstring(response.content).xpath('//ul[@id ="courseMenuPalette_contents"]//a/@href')
    mother_url = 'https://ntulearn.ntu.edu.sg'
    link_collection = [mother_url + link for link in link_collection]

    text_collection = []

    for child in collection:
        text_collection.append(clean_string(child.text_content()))

    # if print_coursemenu_links or True: # remove True
    #     pprint(text_collection)
    #     pprint(link_collection)

    if add_to_folders:
        commit_to_db_folder(text_collection,link_collection,parent_folder=this_folder)

def get_coursemenu_from_mother_links_query_count():

    global db_session

    db_query = db_session.query(Folder).filter(Folder.mother_coursemenu_extracted == 0).filter(Folder.is_mother_link == 1)
    return db_query, db_query.count()

def get_all_coursemenu_from_mother_links():

    global db_session
    db_query, query_count = get_coursemenu_from_mother_links_query_count()

    while query_count > 0:

        for db_row in db_query:

            current_folder_url = db_row.folder_url
            current_folder_path = db_row.folder_path

            try:
                get_coursemenu_text_and_links_from_mother_links(this_url=str(current_folder_url), this_folder=current_folder_path ,print_results=True,print_coursemenu_links=True,add_to_folders=True)
            except:
                e = sys.exc_info()[0]
                pprint(e)
                pprint("Skipping " + str(current_folder_url))
                wait()

            db_row.mother_coursemenu_extracted = 1
            db_session.commit()

        db_query, query_count = get_coursemenu_from_mother_links_query_count()

# ============================================================================================
# MOTHER SUBFOLDER & FILE FUNCTIONS
# ============================================================================================

def get_maincontent_folders_and_files_from_mother_links(this_url, this_folder, print_results=False, print_maincontent_folder_links=False, print_maincontent_file_links=False, add_to_folders=False, add_to_files=False):
    '''
    HTTP GET
    '''
    global requests_session

    # pprint("Running get_maincontent_folders_and_files_from_mother_links")
    # pprint(this_url)

    response = requests_session.get(this_url, timeout=(15,15))
    wait()

    if print_results:
        print_progress(response)

    collection = fromstring(response.content).xpath('//div[@id ="content"]//a')

    file_text_collection = []
    file_link_collection = []

    folder_text_collection = []
    folder_link_collection = []

    for child in collection:
        if "/webapps/blackboard/content/listContent.jsp" in child.attrib['href']:
            # is folder
            folder_text_collection.append(clean_string(child.text_content()))
            folder_link_collection.append(child.attrib['href'])
        elif "/bbcswebdav/" in child.attrib['href']:
            # is file
            file_text_collection.append(clean_file_name(child.text_content()))
            file_link_collection.append(child.attrib['href'])

    mother_url = 'https://ntulearn.ntu.edu.sg'
    file_link_collection = [mother_url + link for link in file_link_collection if mother_url not in link]
    folder_link_collection = [mother_url + link for link in folder_link_collection if mother_url not in link]

    # if print_maincontent_folder_links:
    #     pprint(folder_text_collection)
    #     pprint(folder_link_collection)

    # if print_maincontent_file_links:
    #     pprint(file_text_collection)
    #     pprint(file_link_collection)

    if add_to_folders:
        commit_to_db_folder(folder_text_collection,folder_link_collection,parent_folder=this_folder)

    if add_to_files:
        commit_to_db_file(file_text_collection,file_link_collection,folder_path=this_folder)

def get_subfolders_and_files_from_mother_links_query_count():

    global db_session

    db_query = db_session.query(Folder).filter(Folder.is_mother_link == 1).filter((Folder.files_extracted == 0) | (Folder.subfolders_extracted == 0))
    return db_query, db_query.count()

def get_all_subfolders_and_files_from_mother_links():

    global db_session
    db_query, query_count = get_subfolders_and_files_from_mother_links_query_count()

    while query_count > 0:

        for db_row in db_query:

            current_folder_url = db_row.folder_url
            current_folder_path = db_row.folder_path

            try:
                if db_row.subfolders_extracted == 0 and db_row.files_extracted == 0:
                    # Get folders and files
                    get_maincontent_folders_and_files_from_mother_links(this_url=str(current_folder_url),
                                                                       this_folder=current_folder_path,
                                                                       print_results=True,
                                                                       print_maincontent_folder_links=True,
                                                                       print_maincontent_file_links=True,
                                                                       add_to_folders=True, add_to_files=True)
                elif db_row.subfolders_extracted == 1 and db_row.files_extracted == 0:
                    # Get files only
                    get_maincontent_folders_and_files_from_mother_links(this_url=str(current_folder_url),
                                                                       this_folder=current_folder_path,
                                                                       print_results=True,
                                                                       print_maincontent_folder_links=False,
                                                                       print_maincontent_file_links=True,
                                                                       add_to_folders=False, add_to_files=True)
                elif db_row.subfolders_extracted == 0 and db_row.files_extracted == 1:
                    # Get folders only
                    get_maincontent_folders_and_files_from_mother_links(this_url=str(current_folder_url),
                                                                       this_folder=current_folder_path,
                                                                       print_results=True,
                                                                       print_maincontent_folder_links=True,
                                                                       print_maincontent_file_links=False,
                                                                       add_to_folders=True, add_to_files=False)
            except:
                e = sys.exc_info()[0]
                pprint(e)
                pprint("Skipping " + str(current_folder_url))
                wait()

            db_row.subfolders_extracted = 1
            db_row.files_extracted = 1
            db_session.commit()

        db_query, query_count = get_subfolders_and_files_from_mother_links_query_count()

# ============================================================================================
# CHILD SUBFOLDER & FILE FUNCTIONS
# ============================================================================================

def get_url(this_url):

    global requests_session

    error_msg = None

    for attempt in range(10):
        try:
            response = requests_session.get(this_url, timeout=(15,15)) 
            return response, error_msg
        except requests.exceptions.Timeout as error_msg:
            # Maybe set up for a retry, or continue in a retry loop
            print("Timeout exception! Retrying login...")
            login()
        except requests.exceptions.TooManyRedirects as error_msg:
            # Tell the user their URL was bad and try a different one
            break
        except requests.exceptions.HTTPError as error_msg:
            # Catch 401/404 Errors
            break
        except requests.exceptions.RequestException as error_msg:
            # catastrophic error. bail.
            break
        else:
            # It is useful for code that must be executed if the try clause does not raise an exception
            break
    else:
        # we failed all the attempts - deal with the consequences.
        return None, error_msg

def get_maincontent_folders_and_files_from_child_links(this_url, this_folder, print_results=False, print_maincontent_folder_links=False, print_maincontent_file_links=False, add_to_folders=False, add_to_files=False):
    '''
    HTTP GET
    '''
    global requests_session

    # print("Running get_maincontent_folders_and_files_from_child_links")
    # print(this_url)

    response = requests_session.get(this_url, )
    # response, error_msg = get_url(this_url)
    # if not error_msg == None:
    wait()

    if print_results:
        print_progress(response)

    collection = fromstring(response.content).xpath('//div[@id ="content"]//a')

    file_text_collection = []
    file_link_collection = []

    folder_text_collection = []
    folder_link_collection = []

    for child in collection:
        if "/webapps/blackboard/content/listContent.jsp" in child.attrib['href']:
            # is folder
            folder_text_collection.append(clean_string(child.text_content()))
            folder_link_collection.append(child.attrib['href'])
        elif "/bbcswebdav/" in child.attrib['href']:
            # is file
            file_text_collection.append(clean_file_name(child.text_content()))
            file_link_collection.append(child.attrib['href'])

    mother_url = 'https://ntulearn.ntu.edu.sg'
    file_link_collection = [mother_url + link for link in file_link_collection if mother_url not in link]
    folder_link_collection = [mother_url + link for link in folder_link_collection if mother_url not in link]

    # if print_maincontent_folder_links:
    #     pprint(folder_text_collection)
    #     pprint(folder_link_collection)

    # if print_maincontent_file_links:
    #     pprint(file_text_collection)
    #     pprint(file_link_collection)

    if add_to_folders:
        commit_to_db_folder(folder_text_collection,folder_link_collection,parent_folder=this_folder)

    if add_to_files:
        commit_to_db_file(file_text_collection,file_link_collection,folder_path=this_folder)

def get_subfolders_and_files_from_child_links_query_count():

    global db_session

    db_query = db_session.query(Folder).filter(Folder.is_mother_link == 0).filter((Folder.files_extracted == 0) | (Folder.subfolders_extracted == 0))
    return db_query, db_query.count()

def get_all_subfolders_and_files_from_child_links():

    global db_session
    db_query, query_count = get_subfolders_and_files_from_child_links_query_count()

    while query_count > 0:

        for db_row in db_query:

            current_folder_url = db_row.folder_url
            current_folder_path = db_row.folder_path

            try:
                if db_row.subfolders_extracted == 0 and db_row.files_extracted == 0:
                    # Get folders and files
                    get_maincontent_folders_and_files_from_child_links(this_url=str(current_folder_url),
                                                                       this_folder=current_folder_path,
                                                                       print_results=True,
                                                                       print_maincontent_folder_links=True,
                                                                       print_maincontent_file_links=True,
                                                                       add_to_folders=True, add_to_files=True)
                elif db_row.subfolders_extracted == 1 and db_row.files_extracted == 0:
                    # Get files only
                    get_maincontent_folders_and_files_from_child_links(this_url=str(current_folder_url),
                                                                       this_folder=current_folder_path,
                                                                       print_results=True,
                                                                       print_maincontent_folder_links=False,
                                                                       print_maincontent_file_links=True,
                                                                       add_to_folders=False, add_to_files=True)
                elif db_row.subfolders_extracted == 0 and db_row.files_extracted == 1:
                    # Get folders only
                    get_maincontent_folders_and_files_from_child_links(this_url=str(current_folder_url),
                                                                       this_folder=current_folder_path,
                                                                       print_results=True,
                                                                       print_maincontent_folder_links=True,
                                                                       print_maincontent_file_links=False,
                                                                       add_to_folders=True, add_to_files=False)
            except:
                e = sys.exc_info()[0]
                pprint(e)
                pprint("Skipping " + str(current_folder_url))
                wait()

            db_row.subfolders_extracted = 1
            db_row.files_extracted = 1
            db_session.commit()

        db_query, query_count = get_subfolders_and_files_from_child_links_query_count()

# ============================================================================================
# DOWNLOAD FUNCTION
# ============================================================================================

class TooManyRetriesCustomException(LookupError):
    pass

def try_get_url(this_url):
    for i in range(10):
        try:
            print("Attempt #%s: Getting %s..." % (i, this_url))
            response = requests_session.get(this_url, timeout=(15,15), stream=True) 
            break
        except Exception as e:
            print("Error: %s" % e)
    else:
        print("TooManyRetriesCustomException")
        raise TooManyRetriesCustomException

    return response

def print_progress_for_download(response):
    print("\n")
    print("[Download] Title: " + get_title(response))
    # print("[Download] Status Code: " + str(response.status_code))
    # print("[Download] Response URL: " + response.url)

def navigate_to_download(this_url, folder_path, print_results=False):
    '''
    HTTP GET
    '''
    global requests_session

    print("Initializing navigate_to_download...")

    response = try_get_url(this_url)

    if print_results:
        print_progress_for_download(response)

    # Check whether to skip downloading of blacklisted file extension or not
    if response.url.split('.')[-1] in blacklisted_file_extensions:
        print("Blacklisted file extension: %s" % response.url.split('.')[-1])
        print("Skipping...")
        return response.url.split('/')[-1], response.url

    print("No errors detected, carrying on to download for %s..." % this_url)
    actual_file_name = download_file_to_folder(response.url, response, folder_path)
    actual_file_url = response.url
    return actual_file_name, actual_file_url

def download_file_to_folder(url, response, folder_path):

    print("\nEntering download_file_to_folder(%s, %s, %s)" % (url,response,folder_path))

    filename = unquote(urlparse(url).path.split("/")[-1]) # clean filename from query
    print("download_file_to_folder()>filename: %s" % filename)
    file_extension = filename.split('.')[-1]
    print("download_file_to_folder()>file_extension: %s" % file_extension)

    filename = clean_string(''.join(filename.split('.')[:-1])) + '.' + file_extension

    if file_extension in blacklisted_file_extensions:
        print("Error: Blacklisted File Extension %s" % file_extension)
        print("Skipping %s ..." % url)
        return filename

    # Initilialize Full Path List
    full_path_list = folder_path.split('\\')
    print("download_file_to_folder()>full_path_list: %s" % '/'.join(full_path_list))
    temp_full_path = os.path.join(os.getcwd(), 'files', *full_path_list)

    # Create Directory
    print("Getting or Creating Directory for %s ..." % temp_full_path)
    create_dir(temp_full_path)

    # Download File
    full_path_list.append(filename)
    final_full_path = os.path.join(os.getcwd(), 'files', *full_path_list)

    # Deal with File Paths which are too long
    if sys.platform == 'win32':
        if len(final_full_path) > 259:
            final_full_path = chr(92) + chr(92) + '?' + chr(92) + final_full_path

    print("Downloading %s ..." % filename)
    print("@ %s" % final_full_path)
    with open(final_full_path, "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)

    print("Download complete for %s!" % filename)

    return filename

def get_undownloaded_files_query_count():

    global db_session

    db_query = db_session.query(File).filter(File.file_downloaded == 0)
    return db_query, db_query.count()

def get_all_undownloaded_files():

    global db_session
    db_query, query_count = get_undownloaded_files_query_count()
    print('get_all_undownloaded_files() > get count for first time')

    while query_count > 0:

        for db_row in db_query:

            this_file_url = db_row.file_url
            print('get_all_undownloaded_files() > this_file_url: %s' % this_file_url)
            this_file_path = db_row.folder_path
            print('get_all_undownloaded_files() > this_file_path: %s' % this_file_path)

            print('get_all_undownloaded_files() > try [block]')
            actual_file_name, actual_file_url = navigate_to_download(this_file_url, this_file_path, print_results=True)
            db_row.file_actual_name = actual_file_name
            db_row.file_actual_url = actual_file_url
            wait()

            print('get_all_undownloaded_files() > exited try/except block')
            db_row.file_downloaded = 1
            db_session.commit()

        db_query, query_count = get_undownloaded_files_query_count()
        print('get_all_undownloaded_files() > get count again')

# ============================================================================================
# DOWNLOAD OPTIONS
# ============================================================================================

def wait():

    global throttle_downloads, throttle_download_max_wait, throttle_download_min_wait

    if throttle_downloads:
        time.sleep(random.randint(throttle_download_min_wait, throttle_download_max_wait))

def init_other_options():

    global throttle_downloads, throttle_download_max_wait, throttle_download_min_wait

    print("\n=============")
    print("Download Options")
    print("=============\n")

    throttle_download_max_wait = None
    throttle_download_min_wait = None
    customise_throttle = False

    user_throttle_downloads = input("Would you like to throttle your downloads (limit the download speed by waiting for a few seconds between downloads) [Y/N]? ")
    if user_throttle_downloads == 'Y' or user_throttle_downloads == 'y':
        throttle_downloads = True

        if not customise_throttle:
            throttle_download_max_wait = 10
            throttle_download_min_wait = 3
            return
    else:
        throttle_downloads = False
        return

    while not type(throttle_download_max_wait) == int:

        try:
            throttle_download_max_wait = int(input("What is your maximum allowed wait time in seconds between downloads [Enter integer from 0 to 9999]? "))
        except:
            pass

    while not type(throttle_download_min_wait) == int:

        try:
            throttle_download_min_wait = int(input("What is your minimum allowed wait time in seconds between downloads [Enter integer from 0 to 9999]? "))
        except:
            pass

# ============================================================================================
# EXECUTE OPTIONS
# ============================================================================================

def init_execute_options():

    print("\n===============")
    print("Execute Options")
    print("===============\n")

    mission_list = []

    user_execute_ALL = input("Would you like to execute everything [Y/N]? ")
    if user_execute_ALL == 'Y' or user_execute_ALL == 'y':
        execute_ALL()
        return

    user_get_all_coursemenu_from_mother_links = input("\nWould you like to get_all_coursemenu_from_mother_links [Y/N]? ")
    if user_get_all_coursemenu_from_mother_links == 'Y' or user_get_all_coursemenu_from_mother_links == 'y':
        mission_list.append(get_all_coursemenu_from_mother_links)

    user_get_all_subfolders_and_files_from_mother_links = input("\nWould you like to get_all_subfolders_and_files_from_mother_links [Y/N]? ")
    if user_get_all_subfolders_and_files_from_mother_links == 'Y' or user_get_all_subfolders_and_files_from_mother_links == 'y':
        mission_list.append(get_all_subfolders_and_files_from_mother_links)

    user_get_all_subfolders_and_files_from_child_links = input("\nWould you like to get_all_subfolders_and_files_from_child_links [Y/N]? ")
    if user_get_all_subfolders_and_files_from_child_links == 'Y' or user_get_all_subfolders_and_files_from_child_links == 'y':
        mission_list.append(get_all_subfolders_and_files_from_child_links)

    user_get_all_undownloaded_files = input("\nWould you like to get_all_undownloaded_files [Y/N]? ")
    if user_get_all_undownloaded_files == 'Y' or user_get_all_undownloaded_files == 'y':
        mission_list.append(get_all_undownloaded_files)

    [mission() for mission in mission_list if not mission == None]

def execute_ALL():

    get_all_courselinks_from_selenium()
    get_all_coursemenu_from_mother_links()
    get_all_subfolders_and_files_from_mother_links()
    get_all_subfolders_and_files_from_child_links()
    get_all_undownloaded_files()

# ============================================================================================
# RESET OPTIONS
# ============================================================================================

def init_reset_options():

    print("\n=============")
    print("Reset Options")
    print("=============\n")

    user_reset_ALL = input("Would you like to reset everything [Y/N]? ")
    if user_reset_ALL == 'Y' or user_reset_ALL == 'y':
        reset_ALL()
        return

    user_reset_NONE = input("Would you like to reset something [Y/N]? ")
    if user_reset_NONE == 'N' or user_reset_NONE == 'n':
        return

    user_reset_Folder_mother_links_coursemenu = input("\nWould you like to reset coursemenu for mother links [Y/N]? ")
    if user_reset_Folder_mother_links_coursemenu == 'Y' or user_reset_Folder_mother_links_coursemenu == 'y':
        reset_Folder_mother_links_coursemenu()

    user_reset_Folder_files_extracted = input("\nWould you like to reset extracted files for all links [Y/N]? ")
    if user_reset_Folder_files_extracted == 'Y' or user_reset_Folder_files_extracted == 'y':
        reset_Folder_files_extracted()

    user_reset_Folder_subfolders_extracted = input("\nWould you like to reset extracted subfolders for all links [Y/N]? ")
    if user_reset_Folder_subfolders_extracted == 'Y' or user_reset_Folder_subfolders_extracted == 'y':
        reset_Folder_subfolders_extracted()

    user_reset_File_downloaded = input("\nWould you like to reset all downloaded files [Y/N]? ")
    if user_reset_File_downloaded == 'Y' or user_reset_File_downloaded == 'y':
        reset_File_downloaded()

def reset_ALL():

    reset_Folder_mother_links_coursemenu()
    reset_Folder_files_extracted()
    reset_Folder_subfolders_extracted()
    reset_File_downloaded()

def reset_ALL_except_downloads():

    reset_Folder_mother_links_coursemenu()
    reset_Folder_files_extracted()
    reset_Folder_subfolders_extracted()

def reset_Folder_mother_links_coursemenu():

    global db_session
    db_query = db_session.query(Folder).filter(Folder.is_mother_link == 1)
    initial_count = db_query.count()

    for db_row in db_query:

        db_row.mother_coursemenu_extracted = 0
        db_session.commit()

    print('reset_Folder_mother_links_coursemenu: %s(s) rows reset.' % initial_count)

def reset_Folder_files_extracted():

    global db_session
    db_query = db_session.query(Folder).filter(Folder.files_extracted == 1)
    initial_count = db_query.count()

    for db_row in db_query:

        db_row.files_extracted = 0
        db_session.commit()

    print('reset_Folder_files_extracted: %s(s) rows reset.' % initial_count)

def reset_Folder_subfolders_extracted():

    global db_session
    db_query = db_session.query(Folder).filter(Folder.subfolders_extracted == 1)
    initial_count = db_query.count()

    for db_row in db_query:

        db_row.subfolders_extracted = 0
        db_session.commit()

    print('reset_Folder_subfolders_extracted: %s(s) rows reset.' % initial_count)

def reset_File_downloaded():

    global db_session
    db_query = db_session.query(File).filter(File.file_downloaded == 1)
    initial_count = db_query.count()

    for db_row in db_query:

        db_row.file_downloaded = 0
        db_session.commit()

    print('reset_File_downloaded: %s(s) rows reset.' % initial_count)

# ============================================================================================
# CREDENTIALS OPTIONS
# ============================================================================================

def init_keyring_options():

    print("\n===============")
    print("Credentials Options")
    print("===============\n")

    user_wants_to_change_credentials = False

    if sys.platform == 'win32': # Windows
        from keyring.backends import Windows
        keyring.set_keyring(Windows.WinVaultKeyring())
    else: # Mac
        from keyring.backends import OS_X
        keyring.set_keyring(OS_X.Keyring())

    if keyring.get_password('system', 'username') == None or keyring.get_password('system', 'username') == None:

        print("\nWelcome Stranger! You have not set your username and/or password. Please set them first.")

        username = input("Username: ")

        password = getpass.getpass("Password: ")

        keyring.set_password('system', 'username', username)
        keyring.set_password('system', 'password', password)

    else:

        username = str(keyring.get_password('system', 'username'))
        password = str(keyring.get_password('system', 'password'))

        change_credentials = input("Welcome back, %s. If you want to change or delete your credentials, key in 'Y' without quotes and return to proceed. Else, simply hit return to continue.\nDo you want to change or delete your credentials [Y/N]? " % username)

        if change_credentials.strip() == 'Y' or change_credentials.strip() == 'y':
            keyring.delete_password('system', 'username')
            keyring.delete_password('system', 'password')
            user_wants_to_change_credentials = True
        elif change_credentials.strip() == '':
            user_wants_to_change_credentials = False
        else:
            user_wants_to_change_credentials = False

    return username, password, user_wants_to_change_credentials

def change_keyring():

    print("\nYou have chosen to reset or change your username and password.")

    username = input("New Username: ")

    password = getpass.getpass("New Password: ")

    keyring.set_password('system', 'username', username)
    keyring.set_password('system', 'password', password)

    username = str(keyring.get_password('system', 'username'))
    password = str(keyring.get_password('system', 'password'))

    print("You have sucessfully changed your username and password!\n")

    return username, password

# ============================================================================================
# MAIN FUNCTION
# ============================================================================================

def get_all_courselinks_from_selenium():

    course_title_list, course_url_list = selenium_get_courses()
    commit_to_db_folder(course_title_list, course_url_list, parent_folder=None)

# ============================================================================================
# FAST AND FURIOUS FUNCTION
# ============================================================================================

def fast_and_furious():

    print("\n===============")
    print("FAST AND FURIOUS")
    print("===============\n")

    one_shot = input("Do you want to do a hassle-free quick run of Blackbox [Y/N]? ")

    if one_shot.strip() == 'Y' or one_shot.strip() == 'y' or one_shot.strip() == '':

        reset_ALL_except_downloads()

        global throttle_downloads, throttle_download_max_wait, throttle_download_min_wait
        throttle_downloads = True
        throttle_download_max_wait = 10
        throttle_download_min_wait = 3

        execute_ALL()

        return True

    else:
        return False

def main():

    print('\n')
    print('__________.__                 __   ___.                 ')
    print('\______   \  | _____    ____ |  | _\_ |__   _______  ___')
    print(' |    |  _/  | \__  \ _/ ___\|  |/ /| __ \ /  _ \  \/  /')
    print(' |    |   \  |__/ __ \\\\  \___|    < | \_\ (  <_> >    < ')
    print(' |______  /____(____  /\___  >__|_ \|___  /\____/__/\_ \\')
    print('        \/          \/     \/     \/    \/            \/')
    print('\n')

    print('Contributors: Jarrett Yeo') # All PRs welcome - Contributors feel free to update your name here once your PR is accepted
    print('\n')

    print('Hit CONTROL and C to exit the program anytime.')

    # =========================================================
    # Initialization - Must always be executed!
    # =========================================================
    global username, password, data_credentials

    username, password, user_wants_to_change_credentials = init_keyring_options()
    if user_wants_to_change_credentials:
        username, password = change_keyring()

    data_credentials = {'user_id': username, 'password': password}

    # =========================================================
    # Initialization - Must always be executed!
    # =========================================================
    global db_session
    intialize_db()

    global requests_session, response # requests session
    requests_session = requests.Session() # requests session
    login()

    if not fast_and_furious():
        init_reset_options()
        init_other_options()
        init_execute_options()

    print("\n===============")
    print("END")
    print("===============\n")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            logging.basicConfig(filename='blackbox.log', level=logging.CRITICAL)
        else:
            logging.basicConfig(filename=os.path.join(os.getcwd(),'blackbox.log'), level=logging.CRITICAL)
        main()
    except Exception as e:
        print('%s: %s' % (str(datetime.datetime.now()), e))
        traceback.print_exc()  # shows what exactly went wrong and in which lines
        logging.critical('%s: %s' % (str(datetime.datetime.now()), e), exc_info=True)

        print("\n***************")
        print("FATAL ERROR")
        print("***************\n")

        quit_error = input('Something has gone wrong. Please check your internet connection or inputs. If you believe this is an error, please raise an issue at https://github.com/jarrettyeo/blackbox-v2/issues along with your "blackbox.log" log file.\n\nHit any key to quit...')
