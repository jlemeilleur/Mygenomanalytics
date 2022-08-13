# Mygenomanalytics
An open source web application that provides complementary analysis using 23andme based on the user's uploaded genome files.

## Description
Mygenomanalytics proposes an interactive interface with sample views that include an attempt to link which trait came from which ancestor and a deep dive into your rare mutations. Mygenomanalytics also includes traits at the forefront of research that have not been the main focus of most bioinformatics companies such as: longevity, mathematical ability, facial morphology and many others.

## Sample views
![View0](https://github.com/jlemeilleur/Mygenomanalytics/blob/main/my_snp_api/static/images/ReadmeExample0.jpg)
![View1](https://github.com/jlemeilleur/Mygenomanalytics/blob/main/my_snp_api/static/images/ReadmeExample1.jpg)
![View2](https://github.com/jlemeilleur/Mygenomanalytics/blob/main/my_snp_api/static/images/ReadmeExample2.jpg)
![View3](https://github.com/jlemeilleur/Mygenomanalytics/blob/main/my_snp_api/static/images/ReadmeExample3.jpg)
![View4](https://github.com/jlemeilleur/Mygenomanalytics/blob/main/my_snp_api/static/images/ReadmeExample4.jpg)

## Features
* Big data parsing module (streaming)
* Handles multiple files upload
* Cookies for better user experience
* Automated cleaning of user data after each session
* Optimized queries and app logic for fast response time
* Integration of persistent data with PostgreSQL on setup
* Data caching
* FAQ view
* Docker containerized
* Serving static files with Nginx
* Takes 5min on initial setup and <30sec for any subsequent upload.

## Installation

Step 0:
Please make sure to have Git and Docker installed.

Step 1:
Go into the directory containing the project.
```
cd Mygenomanalytics
```

Step 2 - configuration:
Create the .env file.
```
cp .env.sample .env
```
In .env, please choose your desired configuration and make sure that SETUP_DATABASE_FLAG=True.

Step 3 - make migrations:
```
docker-compose -f docker-compose.yml run --rm my_snp_api sh -c "python manage.py makemigrations"
```

Step 4 - access localhost:<br />
There are two options here. For Dev mode, please go to Step 4a. For Prod, Step 4b.

Step 4a - Dev mode:
```
docker-compose -f docker-compose.yml up
```
The local server should now be available at http://127.0.0.1:8000

Step 4b - Prod mode:
```
docker-compose -f docker-compose-deploy.yml up
```
The local server should now be available at http://127.0.0.1

Step 5 - setup database:<br />
Please upload your files in the home page on local server. The first upload should take about 5min and will automatically setup the database for you. If you don't know where to find the files, please visit the FAQ page on the local server, which provides detailed instructions.

Step 6 - check your results:<br />
You should now be able to visualize all your results on the website. Please visit each view and make sure the following files have been generated:
* Mygenomanalytics/my_snp_api/static/work/Master_file_default.csv
* Mygenomanalytics/my_snp_api/static/work/temp_freq_default.csv
* Mygenomanalytics/my_snp_api/static/work/temp_rare_default.csv

Step 7 - update configuration:<br />
In .env, please change SETUP_DATABASE_FLAG to False, so that the persistent data doesn't get overriden everytime you upload. This should reduce the upload time to <30sec.











