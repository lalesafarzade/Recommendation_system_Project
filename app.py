from flask import Flask,render_template,session,url_for, redirect
import joblib
from flask_wtf import FlaskForm
from matplotlib.pyplot import title
import numpy as np
import pandas as pd
from wtforms import TextAreaField,SubmitField,SelectField
from flask_bootstrap import Bootstrap
import bz2
import pickle
import requests
#from config import API_Key
import os
#import _pickle as cPickle


def decompress_pickle(file):
  data = bz2.BZ2File(file, "rb")
  data = pickle.load(data)
  return data


cosin_=decompress_pickle('pickles/my_cosin.pbz2') 
indices_dict=joblib.load("pickles/indicess.pkl")
res_dict=joblib.load("pickles/rse_dict.pkl")


res=pd.DataFrame(res_dict)
indices=pd.Series(indices_dict)

def title_maker(indices=indices):
    tuples=[]
    for i in indices.index:
        tuples.append((i,i))
    return tuples


def poster_finder(tmdbId):
    response=requests.get(f'https://api.themoviedb.org/3/movie/{tmdbId}?api_key={os.getenv("HEROKU_KEY",API_Key)}&language=en-US')
    
    data=response.json()
    try:
        poster="https://image.tmdb.org/t/p/w500/"+data['poster_path']
        overview=data['overview']
    except:
        poster="https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=687&q=80"
        overview='No information provided in tmdb API'
    return poster,overview




def recommendation(title, cosine_sim= cosin_,k=10):
    
    sim_scores = list(enumerate(cosine_sim[indices[title]]))
    sim_scores = sorted(sim_scores, key= lambda x : x[1], reverse= True)
    sim_scores = sim_scores[1:k+1]
    movie_indices = [i[0] for i in sim_scores]
    movie_title=[res.iloc[i]['title'] for i in movie_indices]  
    movie_poster=[poster_finder(res.iloc[i]['tmdbId'])[0] for i in movie_indices]
    movie_overview=[poster_finder(res.iloc[i]['tmdbId'])[1] for i in movie_indices]
    movie_score=[round(res.iloc[i]['score'],2) for i in movie_indices]
    return movie_title,movie_poster,movie_overview,movie_score


class Recommender(FlaskForm):
    title=SelectField('title',choices=title_maker(indices=indices))
    number=TextAreaField('number')
    submit=SubmitField('Recommend')


app=Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY']="mysecretkey"

@app.route("/recommender",methods=['GET','POST'])
def index():
    form=Recommender()
    if form.validate_on_submit():
        session['title']=form.title.data
        session['number']=form.number.data
        return redirect(url_for("prediction"))
    return render_template('home.html',form=form) 

@app.route("/prediction")
def prediction():
    title=session['title']
    k=int(session['number'])
    titles,poters,overview,score=recommendation(title, cosine_sim= cosin_,k=k)
    results=[{"titles": i, "poters": j,"overview":l,"score":m} for i, j,l,m in zip(titles, poters,overview,score)]
    return render_template('prediction.html',results=results)

@app.route("/")
def welcome():
    return render_template("index.html")


@app.route("/analysis")
def analysis():
    return render_template("analysis.html")

@app.route("/bestmovies")
def best_movies():
    return render_template("best_movie.html")

if __name__=='__main__':
    app.run(debug=True)