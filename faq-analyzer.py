import csv
import operator
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from utils import format_for_comparison, csv_delimiter, Algorithm, create_similarity_matrix, processed_semesters, print_post
import click


class FAQAnalyzer:

    def process_content(self):
        """Reads in the posts from the specified folder and saves content."""
        for semester in processed_semesters[-self.num_semesters:]:
            with open('posts/' + semester + '/' + self.folder + '.csv') as csv_file:
                reader = csv.DictReader(csv_file, delimiter=csv_delimiter)
                for row in reader:
                    post = row['content']
                    self.content.append(row["content"])
                    format_for_comparison(post)
                    self.processed_content.append(post)
                    self.answers.append(row['i_answer'])

    def create_dictionary(self):
        """Uses content to create a dictionary of words.
           Returns a 2D matrix of each vectorized post."""
        count_vectorizer = CountVectorizer(stop_words='english')
        sparse_matrix = count_vectorizer.fit_transform(self.processed_content)
        doc_term_matrix = sparse_matrix.todense()
        df = pd.DataFrame(doc_term_matrix, 
                    columns=count_vectorizer.vocabulary_, 
                    )
        return df

    def find_similarity(self, matrix):
        """Given the similarity matrix, finds and prints the most similar piazza posts."""
        post_groups = []
        for r in range(len(matrix)):
            group = []
            # starting at r = 1 so that the row is the first value in the group
            for c in range(r, len(matrix)):
                # Note adding .01 for precision. If it is insignificantly greater than 1, we don't care.
                if matrix[r][c] > 1.01:
                    print("Algorithm is buggy. Got a similarity greater than 1")
                    print(matrix[r][c])
                    exit(1)
                # TODO - determine the appropriate measure of 'similar' enough
                #        using 0.6 for now but another number might be better
                if matrix[r][c] > 0.6:
                    group.append(c)
            # if {A, B, C} is a group don't want {B, C} as separate group
            issubset = False
            for g in post_groups:
                if set(group) <= set(g):
                    issubset = True
                    break
            if not issubset:
                post_groups.append(group)
        
        post_groups.sort(key=len, reverse=True)
        
        for group in post_groups[:self.max_post_groups]:
            # Note: since we are not reorganizing the row, the first 
            # value will always be the row
            r = group[0]
            group_with_similarity = []
            for c in group:
                group_with_similarity.append((matrix[r][c], self.content[c]))
            
            sorted_x = sorted(group_with_similarity, reverse=True, 
                              key=operator.itemgetter(0))

            for sim, post in sorted_x[:self.max_posts_per_group]:
                print_post(post, sim)
                print('\n')
            print('-------------------------------------------------------------------')            

    def calculate_faq(self):
        self.reset()
        self.process_content()
        df = self.create_dictionary()
        matrix = create_similarity_matrix(df, df, self.algorithm)
        self.find_similarity(matrix)
    
    def reset(self):
        self.content = []
        self.processed_content = []
        self.answers = []

    def __init__(self, folder, algorithm, num_semesters, max_posts_per_group, max_post_groups):
        self.folder = folder
        self.algorithm = algorithm
        self.num_semesters = num_semesters
        self.max_posts_per_group = max_posts_per_group
        self.max_post_groups = max_post_groups
        self.reset()


@click.command()
@click.option("--folder", "-f", "folder", required=True, help="The folder to search for the question in. Options are: project1, project2, project3, project4, project5, midterm, and final")
@click.option("--algorithm", "-a", "algorithm", default=Algorithm.COSINE_SIMILARITY, type=click.INT, help="The search algorithm to use. The options are: \n\tBag of Words (1)\n\tCosine similarity (2)")
@click.option("--num_semesters", '-ns', "num_semesters", type=click.INT, 
               default=1, help="Number of semesters to include while generating the Frequently Asked Questions.")
@click.option("--max_posts_per_group", "-mpg", type=click.INT, default=5,
              help="Max number of posts printed as similar with another post. This field helps limit the output.")
@click.option("--max_post_groups", "-msp", type=click.INT, default=5,
              help="Max number of similar posts groupings to print. This field helps limit output.")
def main(folder, algorithm, num_semesters, 
         max_posts_per_group, max_post_groups):
    if num_semesters > len(processed_semesters):
        print(f'Num semesters is too big. Max number of ' +
            f'semesters is {len(processed_semesters)}')
        exit(1)
    faq = FAQAnalyzer(folder, algorithm, num_semesters, 
                      max_posts_per_group, max_post_groups)
    faq.calculate_faq()


if __name__ == "__main__":
    main()