import requests
from collections import defaultdict
import json
import os
from dotenv import load_dotenv

load_dotenv()

myun = str(os.getenv('GITHUB_USERNAME'))
mypw = str(os.getenv('GITHUB_ACCESS_TOKEN'))

my_starred_repos = []
my_starred_users = []

# Dictionary to store user -> [starred repos] mapping
user_starred_repos = defaultdict(set)

def get_starred_by_user(user_name, starred_repos):
    starred_resp_list = []
    last_resp = None
    first_url_to_get = f'https://api.github.com/users/{user_name}/starred'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    
    try:
        first_url_resp = requests.get(first_url_to_get, auth=(myun, mypw), headers=headers)
        if first_url_resp.status_code != 200:
            print(f"Error fetching starred repos for {user_name}: {first_url_resp.status_code} {first_url_resp.reason}")
            return
        
        last_resp = first_url_resp
        starred_resp_list.append(first_url_resp.json())
        
        while last_resp.links.get('next'):
            next_url_to_get = last_resp.links['next']['url']
            next_url_resp = requests.get(next_url_to_get, auth=(myun, mypw), headers=headers)
            if next_url_resp.status_code != 200:
                print(f"Error fetching next page for {user_name}: {next_url_resp.status_code} {next_url_resp.reason}")
                break
            last_resp = next_url_resp
            starred_resp_list.append(next_url_resp.json())
        
        for page in starred_resp_list:
            for repo in page:
                if isinstance(repo, dict) and 'html_url' in repo:
                    sr = repo['html_url']
                    starred_repos.append(sr)
    except Exception as e:
        print(f"Error in get_starred_by_user for {user_name}: {e}")


def get_starred_repo_users(starred_repos, starred_users):
    for ln in starred_repos:
        right_split = ln.split('.com/')[1]
        starred_usr = right_split.split('/')[0]
        starred_users.append(starred_usr)

# Get starred repos for all users in the list
def get_starred_repos_for_users(users, user_starred_repos):
    for user in users:
        repos = []
        try:
            get_starred_by_user(user, repos)
            user_starred_repos[user].update(repos)
        except Exception as e:
            print(f"Error fetching starred repos for user {user}: {e}")

# Compute Jaccard similarity between two users
def jaccard_similarity(user1, user2, user_starred_repos):
    repos1 = user_starred_repos[user1]
    repos2 = user_starred_repos[user2]
    intersection = len(repos1 & repos2)
    union = len(repos1 | repos2)
    return intersection / union if union != 0 else 0

# Recommend repositories
def recommend_repos(my_user, user_starred_repos):
    scores = {}
    for user, repos in user_starred_repos.items():
        if user != my_user:
            similarity = jaccard_similarity(my_user, user, user_starred_repos)
            for repo in repos:
                if repo not in user_starred_repos[my_user]:
                    if repo not in scores:
                        scores[repo] = 0
                    scores[repo] += similarity
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

get_starred_by_user(myun, my_starred_repos)
get_starred_repo_users(my_starred_repos, my_starred_users)
get_starred_repos_for_users(my_starred_users, user_starred_repos)
recommendations = recommend_repos(myun, user_starred_repos)

print("Recommended repositories:")
for repo, score in recommendations[:10]:  # Top 10 recommendations
    print(f"{repo} (score: {score:.2f})")
