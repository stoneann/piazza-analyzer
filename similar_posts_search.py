import csv
import numpy as np
import queue
from sklearn.metrics.pairwise import cosine_similarity
import click 
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from utils import format_for_comparison, folders, Algorithm, processed_semesters, csv_delimiter, print_post, create_similarity_matrix


class Searcher:

    def convert_similarity_score(self, number):
        """Converts the similarity score to be a max is most similar
            instead of min being most similar."""
        return 1 - number

    def calculate_similarity(self, input_question, comparison_content):
        """Takes an input question and all data to compare against
            and returns a comparison matrix using the desired algorithm."""
        count_vectorizer = CountVectorizer(stop_words='english')
        sparse_matrix = count_vectorizer.fit_transform(comparison_content)
        doc_term_matrix = sparse_matrix.todense()
        transformed_q = count_vectorizer.transform([input_question]).todense()
        question_df = pd.DataFrame(transformed_q, 
                    columns=count_vectorizer.vocabulary_, 
                    )
        df = pd.DataFrame(doc_term_matrix, 
                    columns=count_vectorizer.vocabulary_, 
                    )
        return create_similarity_matrix(question_df, df, self.algorithm)
        
    def print_top_results(self):
        """Prints the most similar posts."""
        if self.top_results.qsize() == 0:
            print('No results')
            return
        for i in range(self.num_results):
            if self.top_results.qsize() == 0:
                return
            similar_score, question, i_answer, s_answer = self.top_results.get()
            similar_score = self.convert_similarity_score(similar_score)
            print(f'\nResult #{i}')
            print_post(question, similar_score=similar_score, n=self.n, i_answer=i_answer, s_answer=s_answer)

    def find_similar_questions(self):
        """Finds similar questions for the self.question variable and
            prints the results."""
        content_question = []
        instructor_answers = []
        student_answers = []
        processed_content_question = []
        for semester in processed_semesters:
            with open('posts/' + semester + '/' + self.folder + '.csv') as csv_file:
                reader = csv.DictReader(csv_file, delimiter=csv_delimiter)
                for row in reader:
                    comparison_question = row['content']
                    content_question.append(comparison_question)
                    processed_content_question.append(format_for_comparison(comparison_question))
                    instructor_answers.append(row['i_answer'])
                    student_answers.append(row['s_answer'])
                    # calculate the similarity
        similarity = self.calculate_similarity(self.question, processed_content_question)
        self.top_results = queue.PriorityQueue()
        for index, similar_score in enumerate(similarity):
            if similar_score > 0.1:
                similar_score = self.convert_similarity_score(similar_score)
                self.top_results.put((similar_score, content_question[index], instructor_answers[index], student_answers[index]))
        self.print_top_results()
    
    def set_question(self, project, question):
        """Set a question to find similar posts for and
            which folder to search in."""
        self.folder = project
        self.question = question
    
    def __init__(self, project, question, num_results, max_print_length = 79, algorithm = 1):
        self.algorithm = algorithm
        self.num_results = num_results
        self.set_question(project, question)
        self.n = max_print_length


@click.command()
@click.option("--num_results", "-nr", "num_results", default=10, help="Number of search results to display")
@click.option("--question", "-q", "question", required=True, type=click.STRING, help="The piazza question to search for")
@click.option("--algorithm", "-a", "algorithm", default=Algorithm.COSINE_SIMILARITY, type=click.INT, help="The search algorithm to use. The options are: \n\tBag of Words (1)\n\tCosine similarity (2)")
@click.option("--folder", "-f", "folder", required=True, help="The folder to search for the question in. Options are: project1, project2, project3, project4, project5, midterm, and final")
@click.option("--max_print_length", "-mpl", "max_print_length",default=79, help="The maximum print length of the output before running onto the next line.")
def main(num_results, question, algorithm, folder, max_print_length):
    if folder not in folders:
        print(f"Not a valid folder. Options are: project1, project2, project3, project4, project5, midterm, and final.")
        exit(1)
    classifier = Searcher(project=folder, question=question, num_results=num_results, max_print_length=max_print_length, algorithm=algorithm)
    classifier.find_similar_questions()
    return


if __name__ == "__main__":
    main()