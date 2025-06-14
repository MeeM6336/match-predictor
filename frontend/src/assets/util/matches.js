import axios from 'axios'

export const fetchUpcomingMatches =  async(modelId) => {
    try {
      const response = await axios.get(`http://localhost:3000/upcoming/${modelId}`);
      return response.data;
    } catch(err) {
      console.log('Error getting upcoming matches: ', err.message);
      return [];
    };
};

export const fetchMatchPredictionStats = async(modelId) => {
    try {
      const response = await axios.get(`http://localhost:3000/upcomingstats/${modelId}`);
      return response.data;
    } catch(err) {
      console.log('Error getting match prediction stats: ', err.message);
      return [];
    };
};

export const fetchModelMetrics = async (modelName) => {
    try {
      const response = await axios.get(`http://localhost:3000/metrics/${modelName}`);
      return response.data;
    } catch(err) {
      console.log('Error getting model metrics: ', err.message);
      return [];
    };
};

export const fetchFeatureVectors = async () => {
  try {
    const response = await axios.get("http://localhost:3000/livefeaturevectors");
    return response.data;
  } catch(err) {
    console.log('Error feature vectors: ', err.message);
    return [];
  };
}

export const fetchTrainingDatasetStats = async (model_id) => {
  try {
    const response = await axios.get(`http://localhost:3000/trainingdatasetstats/${model_id}`);
    return response.data;
  } catch(err) {
    console.log('Error getting training dataset stats: ', err.message);
      return [];
  };
};

export const fetchLiveDatasetStats = async (model_id) => {
  try {
    const response = await axios.get(`http://localhost:3000/livedatasetstats/${model_id}`);
    return response.data;
  } catch(err) {
    console.log('Error getting live dataset stats: ', err.message);
      return [];
  };
};

export const fetchModels = async () => {
  try {
    const response = await axios.get('http://localhost:3000/models');
    return response.data;
  } catch(err) {
    console.log('Error model id/name: ', err.message);
      return [];
  };
};