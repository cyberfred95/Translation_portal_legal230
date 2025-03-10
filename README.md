# Translation_portal_legal230

```
sudo ssh -i ~/.ssh/console-prod.pem ubuntu@3.77.34.25 
```


## Project setup

### Requirements

1) Docker (we have version 24.0.7)
2) docker-compose (2.+)
3) Server machine OS: Ubuntu

### Creating a database dump

Notice: If you don`t have portal on your machine you can skip this part


first of all, if you already have a running portal and you need to update 
it you need to create a db dump to protect your data and for this you need to go to db container

1) to display a list of all containers execute this command in your terminal:

```
docker ps
```

2) copy the id of db container and execute this command:

```
docker exec -it <db_docker_container_id> bash
```

instead of <db_docker_container_id> paste the real id of db container

3) create a db dump execute this command:

```
pg_dump -U <db_user> -d <db_name> > <year>_<month>_<day>.sql
```

instead if <year>_<month>_<day> paste current date. You can choose another file name if you want but I will use ```<year>_<month>_<day>.sql``` as an example.
Your ```<db_user>``` and ```<db_name>``` are in docker-compose.prod.yaml file

4) to exit db container type this command:

```
exit
```

You created a db dump inside docker container, so it is not on your server.
5) move your dump file from docker container to server you should use this command:

```
docker cp <db_docker_container_id>:<year>_<month>_<day>.sql /home/ubuntu/<year>_<month>_<day>.sql
```

This one copies dump file to your local machine to a path you gave. I show standard AWS Lightsail instance path as an example

Now when you have a backup you have an ability to revert everything and save your working version

### Set new files
1) Move a zip file you received to a server using this command:

```
scp </Users/user/Doucments/portal.zip> <your_server_connect>:<your_server_path>
```

2) unzip the portal files using this command:

```
unzip portal_files.zip
```

If you don't have unzip package on your server
use this command and try unzipping the files again:

```
sudo apt-get install unzip
```

3) Go to unzipped files directory and enter a main module (it contains ```settings.py``` file)
and open a settings file using this command:

```
sudo nano settings.py
```
4)  find and ```ALLOWED_HOSTS``` config and add there a url you want to use for your portal

### Crate Nginx configurations

Note: You can skip this step if you already configured Nginx for your portal

1) If you don't have Nginx on your server, please run this command:

```
sudo apt update
sudo apt install nginx
```

2) Navigate to directory with Nginx config files:

```
cd /etc/nginx/sites-available
```

3) Create a new config file for your portal

```
touch <portal_name>
```
4) Copy an example file content to your config 
Here is an example file:

```
server {
    server_name <your_domain>;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    client_max_body_size 30M;

    location / {
          proxy_pass http://localhost:<your_runserver_container_port>;
          proxy_set_header Host $http_host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias <path_to_your_files>/static_collected/;
    }

    location /media/ {
        alias <path_to_your_files>/media/;
    }
}
```

5) check if configuration is correct:

```
sudo nginx -t
```
If not please correct all the mistakes

6) Link your config file to available websites on your server


```
sudo ln -s /etc/nginx/sites-available/<your_portal> /etc/nginx/sites-available/
```

7) Restart the server to apply changes:

```
sudo systemctl restart nginx 
```

or 

```
sudo systemctl restart nginx.service
```

8) If you want to use https url you also need Certbot for it

to install Certbot please follow instructions on this website: https://certbot.eff.org/

9) When you installed a certbot, use this command to set https to url for your portal and receive ssl certificate:

```
sudo certbot --nginx
```

10) Then check if configurations are correct and restart Nginx to apply changes

### Start project

1) Go to your project directory
2) Type this command to start the project:

```
docker-compose -f docker-compose.prod.yaml up
```
3) Open another terminal and connect to your server
4) type ```docker ps``` and go into runserver container using ```docker exec``` command like it was shown before
5) Type this command to collect static files (.css and .js):
```
python manage.py collectstatic --no-input
```

#### If did not have a portal before

1) display list of your docker containers using ```docker ps``` command 
2) Type this command to enter runserver container:

```
docker exec -it <runserver_docker_container_id> bash
```
3) Run migrations:
```
python manage.py migrate
```
4) create a super user for administration:
```
python manage.py createsuperuser
```
Enter your username, email and password to create a super user
5) Run the ```python manage.py collectstatic --no-input``` to set your static files (.html, .css, .js)

6) Go to your portal url and add ```/admin/``` in the end, and type your username and password 

#### If you already have a portal

1) get a list of all containers on your server using ```docker ps``` command
2) Copy a db dump to your db container:

```
docker cp /path/to/your/dump.sql <db_container_id>:dump.sql
```

3) enter a db container using ```docker exec -it <db_container> bash```
4) Import the db dump using the following command

```
psql -U <db_user> -d <db_name> < dump.sql
```
5) Run the migrations to add new fields using ```python manage.py migrate ``` command inside runserver container
6) Run the ```python manage.py collectstatic --no-input``` to set your static files (.html, .css, .js)
