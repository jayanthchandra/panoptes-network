Get Observations Data
=====================

Type: [Google Cloud Function](https://cloud.google.com/functions/)
Purpose: Retrieve observations metadata, either from database or existing json file.
Name: header-to-metadb
Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/get-observations-data
Payload Example: 

	```
	{ "header": fits_header }
	```

Environment Variables:

	:warning: You must set the environment varibales via the web interface.

	POSTGRES_PASSWORD: Password for the metadata database.


Deploy
------
[Offical Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From current directory:

```bash
gcloud functions deploy get-observations-data \
	--entry-point get_observations_data \
	--runtime python37 \
	--trigger-http