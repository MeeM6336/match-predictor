import axios from 'axios'

export const fetchUpcomingMatches =  async() => {
    try {
        const response = await axios.get('http://localhost:3000/upcoming');
        return response.data;
    } catch(err) {
        console.log('Error getting upcoming matches: ', err.message);
        return [];
    }
}

export const fetchMatchPredictionStats = async() => {
    try {
        const response = await axios.get('http://localhost:3000/upcomingstats');
        return response.data;
    } catch(err) {
        console.log('Error getting match predicition stats: ', err.message);
        return [];
    }
}

export const fetchModelMetrics = async (modelName, modelDate) => {
    try {
        const response = await axios.get(`http://localhost:3000/metrics/${modelName}/${modelDate}`);
        return response.data;
    } catch(err) {
        console.log('Error getting model metrics: ', err.message);
        return [];
    }
}

export function heatMap() {

}