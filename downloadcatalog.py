import bs4
import requests
import pandas as pd
import numpy as np
import re
from time import sleep

# Initialize URL and get links
BASE_URL = "http://collegecatalog.uchicago.edu"

catelog = requests.get("http://collegecatalog.uchicago.edu/thecollege/programsofstudy/")
soup = bs4.BeautifulSoup(catelog.text)
link_finder = soup.find("ul", class_="nav leveltwo")
course_urls = [BASE_URL + link['href'] for link in link_finder.find_all("a")]

def extract_course_data(url):
    '''Gets initial title, descriptionm, and detail data from html blocks'''
    response = requests.get(url)
    page_soup = bs4.BeautifulSoup(response.text, features="lxml")
    sections = ["sc_sccoursedescs", "courses", "sc_courseblock", "courseblock main"]
    course_blocks = page_soup.find_all("div", class_=sections)
    if not course_blocks:
        return None
    titles, descs, details = [], [], []
    for block in course_blocks:
        titles += block.find_all("p", class_="courseblocktitle")
        descs += block.find_all("p", class_="courseblockdesc")
        details += block.find_all("p", class_="courseblockdetail")
    return titles, descs, details

# FInds resepctive field (name, instructor, number, etc.) details from original data extraction
def parse_course_titles(items):
    numbers = [re.search(r'\b\d+\b', item.get_text()).group() for item in items]
    names = [re.findall(r'\.(.*?)(?=\.)', item.get_text())[0].strip().replace("100 Units", "") if re.findall(r'\.(.*?)(?=\.)', item.get_text()) else np.nan for item in items]
    return numbers, names

def parse_course_descriptions(items):
    return [item.get_text().strip() for item in items]

def parse_course_details(items):
    instructors, terms, equivalents, prerequisites = [], [], [], []
    for item in items:
        term_detail = re.search(r'(?<=Terms Offered: )(.*)\n', item.get_text())
        instructor_detail = re.search(r'(?<=Instructor\(s\): )(.*)\s\s\s', item.get_text())
        terms.append(term_detail.group().strip() if term_detail else None)
        instructors.append(instructor_detail.group().strip() if instructor_detail else None)
        equivalent_detail = re.search(r'(?<=Equivalent Course\(s\): )(.*)', item.get_text())
        prereq_detail = re.search(r'(?<=Equivalent Course\(s\): )(.*)\n', item.get_text())
        equivalents.append(equivalent_detail.group() if equivalent_detail else None)
        prerequisites.append(prereq_detail.group() if prereq_detail else None)
    return instructors, terms, equivalents, prerequisites

# Loops over link to find data for everything
course_data = pd.DataFrame()
for url in course_urls:
    sleep(3)  
    course_info = extract_course_data(url)
    if course_info:
        title_data, desc_data, detail_data = course_info
        course_nums, course_names = parse_course_titles(title_data)
        course_descs = parse_course_descriptions(desc_data)
        course_instructors, course_terms, course_equivs, course_prereqs = parse_course_details(detail_data)

        min_length = min(len(course_nums), len(course_names), len(course_descs), len(course_instructors), len(course_terms), len(course_equivs), len(course_prereqs))
        temp_data_frame = pd.DataFrame({
            "Department": [title_data[0].get_text()[:4]] * min_length,
            "Course Number": course_nums[:min_length],
            "Course Name": course_names[:min_length],
            "Description": course_descs[:min_length],
            "Instructors": course_instructors[:min_length],
            "Terms Offered": course_terms[:min_length],
            "Equivalent Courses": course_equivs[:min_length],
            "Prerequisites": course_prereqs[:min_length]
        })

        print(temp_data_frame["Department"].unique())
        course_data = pd.concat([course_data, temp_data_frame], ignore_index=True)

course_catelog_df = course_data[course_data["Instructors"] != "DROP"]
course_catelog_df.to_csv("course_catelog.csv")

# Code to create Department.csv
unique_count = course_catelog_df['Department'].value_counts()

department_df = unique_count.reset_index()
department_df.columns = ['Department', 'Unique Classes']

department_df.to_csv("department.csv", index=False)

# Random code to help answer some of the Hw questions
course_catalog_df = pd.read_csv(r"C:\Users\aidan\hw4-ajace13\course_catelog.csv")

course_counts = course_catalog_df["Course Name"].value_counts()

name_duplicates = course_counts[course_counts > 1]
name_duplicates.sum()

unique_count = course_catalog_df['Department'].value_counts()

course_catalog_df.describe()

season_offered = course_catalog_df["Terms Offered"].value_counts()

