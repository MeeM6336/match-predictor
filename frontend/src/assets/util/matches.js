import axios from 'axios'

export const fetchUpcomingMatches =  async() => {
    try {
      const response = await axios.get('http://localhost:3000/upcoming');
      return response.data;
    } catch(err) {
      console.log('Error getting upcoming matches: ', err.message);
      return [];
    };
};

export const fetchMatchPredictionStats = async() => {
    try {
      const response = await axios.get('http://localhost:3000/upcomingstats');
      return response.data;
    } catch(err) {
      console.log('Error getting match predicition stats: ', err.message);
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

export const fetchTrainingDatasetStats = async () => {
  try {
    const response = await axios.get('http://localhost:3000/trainingdatasetstats');
    return response.data;
  } catch(err) {
    console.log('Error getting training dataset stats: ', err.message);
      return [];
  };
};

export const fetchLiveDatasetStats = async () => {
  try {
    const response = await axios.get('http://localhost:3000/livedatasetstats');
    return response.data;
  } catch(err) {
    console.log('Error getting live dataset stats: ', err.message);
      return [];
  };
};

export function computeRocAuc(y_true, y_prob) {
  const data = y_true.map((label, idx) => ({ label, prob: y_prob[idx] }));

  data.sort((a, b) => b.prob - a.prob);

  let tp = 0;
  let fp = 0;
  const tps = [];
  const fps = [];

  const P = y_true.filter(y => y === 1).length;
  const N = y_true.filter(y => y === 0).length;

  for (const point of data) {
    if (point.label === 1) {
      tp++;
    } else {
      fp++;
    }
    tps.push(tp);
    fps.push(fp);
  };

  const tpr = tps.map(v => v / P);
  const fpr = fps.map(v => v / N);

  let auc = 0;
  for (let i = 1; i < tpr.length; i++) {
    const width = fpr[i] - fpr[i - 1];
    const height = (tpr[i] + tpr[i - 1]) / 2;
    auc += width * height;
  };

  return auc;
};