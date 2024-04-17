import csv
from utils import csv_delimiter
import click

@click.command()
@click.option("--semester", "-s", "semester", type=click.STRING,
              required=True, help="Piazza username.")
@click.option("--folder", "-f", "folder", type=click.STRING,
              required=True, help="Piazza password.")
def main(semester, folder):
    words = {}
    word_num_posts = {}
    with open('posts/' + semester + '/' + folder + '.csv') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=csv_delimiter)
        for row in reader:
            post = row['content']
            post_words = post.split(' ')
            for word in post_words:
                if words.get(word) is None:
                    words[word] = 1
                else:
                    words[word] += 1
            for word in set(post_words):
                if word_num_posts.get(word) is None:
                    word_num_posts[word] = 1
                else:
                    word_num_posts[word] += 1
    
    with open('word_frequency/' + semester + '/' + folder + '.csv', 'w') as csvfile:
        fieldnames = ['word', 'count', 'num_posts']
        filewriter = csv.DictWriter(csvfile, delimiter=csv_delimiter, fieldnames=fieldnames)
        # filewriter.writeheader()
        for word, cnt in words.items():
            filewriter.writerow({'word': word, 'count': cnt, 'num_posts': word_num_posts[word]})
        

if __name__ == "__main__":
    main()