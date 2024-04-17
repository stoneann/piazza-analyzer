from datetime import datetime
import re
import html
import string
# from sklearn.metrics.pairwise import cosine_similarity
# from enum import StrEnum, IntEnum
# import numpy as np


# class Folders(StrEnum):
#     PROJECT1 = 'project1',
#     PROJECT2 = 'project2',
#     PROJECT3 = 'project3',
#     PROJECT4 = 'project4',
#     PROJECT5 = 'project5',
#     MIDTERM = 'midterm',
#     FINAL = 'final'


# class Algorithm(IntEnum):
#     BAG_OF_WORDS = 1,
#     COSINE_SIMILARITY = 2


# folders = [Folders.PROJECT1, Folders.PROJECT2, Folders.PROJECT3, Folders.PROJECT4, Folders.PROJECT5, Folders.MIDTERM, Folders.FINAL]


csv_delimiter = '|'


processed_semesters = ['F21', 'W22', 'F22', 'W23']


def parse_time(time):
    format = "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(time,format)


def preprocess_content(content):
    CLEANR = re.compile('<.*?>') 
    return html.unescape(re.sub(CLEANR, '', content).replace("\n", ". "))


def format_for_comparison(content):
    # translate the words into lower case and get rid of punctation
    # so that the algorithm better detects similar words
    return content.lower().translate(str.maketrans('', '', string.punctuation))


# def create_similarity_matrix(df_1, df_2, algorithm):
#     if algorithm == Algorithm.COSINE_SIMILARITY:
#         return cosine_similarity(df_1, df_2).T
#     elif algorithm == Algorithm.BAG_OF_WORDS:
#         dotted_matrix = np.dot(df_1, df_2.T)
#         sums = np.array([np.diag(dotted_matrix)] * len(dotted_matrix)).T
#         return np.divide(dotted_matrix, sums)
#     else:
#         print("Not a valid algorithm")
#         exit(1)


# def print_post(question, similar_score, n = 79, i_answer = "", s_answer=""):
#     print(f'Similarity - \n\t{similar_score}')
#     print('Question -')
#     question_pieces = [question[i:i+n] for i in range(0, len(question), n)]
#     print('\t' + '\n\t'.join(question_pieces))
#     if i_answer != "":
#         print('Instructor Answer - ')
#         i_answer_pieces = [i_answer[i:i+n] for i in range(0, len(i_answer), n)]
#         print('\t' + '\n\t'.join(i_answer_pieces))
#     if s_answer != "":
#         print('Student Answer - ')
#         s_answer_pieces = [s_answer[i:i+n] for i in range(0, len(s_answer), n)]
#         print('\t' + '\n\t'.join(s_answer_pieces))