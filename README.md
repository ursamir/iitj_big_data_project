# Collaborative Filtering for Netflix Movie Recommendations

This project aims to develop a movie recommendation system for Netflix using collaborative filtering techniques to predict user preferences based on their past ratings and behavior.

## Project members

* Samir Kumar Mishra - G23AI1052
* Ashish Kumar - G23AI1005
* Prudhivi Rachan Kumar Sai - G23AI1030

## Overview

Collaborative filtering relies on the concept that people who liked something in the past would also like the same experience in future. This project aims to develop a movie recommendation system for Netflix using collaborative filtering techniques to predict user preferences based on their past ratings and behavior. The primary goal is to enhance the user experience by providing personalized movie recommendations. This project will utilize the Netflix dataset, which contains a large volume of user rating data, and will apply big data analytics to derive meaningful insights and accurate predictions.

## Methodology

1. **Data Ingestion**:
   - Apache Kafka on Docker (optional)
     - Purpose: Stream user interactions and new ratings in real-time.
     - Setup: Use Docker to run Kafka locally or on a cloud VM with free credits (like Google Cloud or AWS Free Tier).
   - Spark connector for MongoDB
     - Purpose: Stream existing user rating data to process.
     - Setup: Ran Spark on Google Colab.

2. **Data Storage**:
   - Personal MongoDB Cloud:
     - Purpose: Store historical data, batch data, movie data, model data.
     - Setup: Connected the Spark application to MongoDB instance hosted on personal cloud.
   - Personal Redis Cloud:
     - Purpose: Cache stored model data, movie data, and IMDB images (optional) and serve low-latency recommendations.
     - Setup: Connected Spark application to the Redis instance hosted on personal cloud.

3. **Data Processing and Model Creation**:
   - Apache Spark on Google Colab:
     - Purpose: Process historical ratings to create model for prediction and to batch process updated ratings to update the model.
     - Setup: Used Google Colab to run Spark jobs.

4. **Model Serving**:
   - Streamlit Application:
     - Purpose: Serve real-time recommendations based on model prediction.
     - Setup: Hosted the application on personal cloud.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
