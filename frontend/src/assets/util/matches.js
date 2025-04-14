import axios from 'axios'

export const fetchUpcomingMatches =  async() => {
    try {
        const response = await axios.get('http://localhost:3000/upcoming');
        return response.data;
    } catch(err) {
        console.log("Error getting upcoming matches: ", err.message);
        return [];
    }
}
