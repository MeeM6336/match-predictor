import React, { useState, useEffect, useMemo } from 'react';
import { fetchUpcomingMatches, fetchMatchPredictionStats } from '../assets/util/matches';
import './MatchPredictions.css'

const MatchPredictions = ({model}) => {
  const [upcomingMatchList, setUpcomingMatchList] = useState([]);
	const [filterType, setFilterType] = useState(1)
	const [searchQuery, setSearchQuery] = useState('');

	const selectFilter = (event) => {
    setFilterType(event.target.value);
  };

  const getDate = (dateString) => {
      const date = new Date(dateString);
  
      const localString = date.toLocaleString('en-US', {
        timeZone: 'America/Chicago',
        year: '2-digit',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
  
      return localString
    };
	
	const renderMetric = (value, name) => (
    <div className='performance-metric'>
      <p className='performance-metric-number'>{typeof value === 'number' ? value.toFixed(4) : 'N/A'}</p>
      <p className='performance-metric-name'>{name}</p>
    </div>
  );
  
	useEffect(() => {
		const loadMatches = async () => {
			const matches = await fetchUpcomingMatches(model.model_id);
			const filteredMatches = matches.filter(match => match.tournament_type >= filterType);

			setUpcomingMatchList(filteredMatches);
		};

		loadMatches();
	}, [model?.model_id, filterType]);

	const finalFilteredMatches = useMemo(() => {
    if (!searchQuery) {
      return upcomingMatchList;
    }

    const lowerCaseSearchQuery = searchQuery.toLowerCase();

    return upcomingMatchList.filter(match =>
      match.team_a.toLowerCase().includes(lowerCaseSearchQuery) ||
      match.team_b.toLowerCase().includes(lowerCaseSearchQuery)
    );
  }, [upcomingMatchList, searchQuery]);

	const matchMetrics = useMemo(() => {
		let t_neg = 0, t_pos = 0, f_neg = 0, f_pos = 0;
		const y_true = [];
		const y_prob = [];

		finalFilteredMatches.forEach(match => {
			const { actual_outcome, prediction, confidence } = match;
			if (actual_outcome != null && prediction != null && confidence != null) {
				y_true.push(actual_outcome);
				y_prob.push(confidence);

				if (prediction === 1 && actual_outcome === 1) t_pos++;
				else if (prediction === 1 && actual_outcome === 0) f_pos++;
				else if (prediction === 0 && actual_outcome === 0) t_neg++;
				else if (prediction === 0 && actual_outcome === 1) f_neg++;
			}
		});

		const total = t_pos + t_neg + f_pos + f_neg;

    const accuracy = total > 0 ? (t_pos + t_neg) / total : 0;
    const precision = (t_pos + f_pos) > 0 ? t_pos / (t_pos + f_pos) : 0;
    const recall = (t_pos + f_neg) > 0 ? t_pos / (t_pos + f_neg) : 0;
    const f1 = (precision + recall) > 0 ? (2 * precision * recall) / (precision + recall) : 0;

		return({ "accuracy": accuracy, "f1": f1 });
	}, [finalFilteredMatches])


  return (
    <div className='MatchPredictions'>
			<div className='match-predictions-header'>
				<p className='match-prediction-title'>All Match Predictions</p>
				<div className='metrics-container'>
						{renderMetric(matchMetrics.accuracy, 'Accuracy')}
						{renderMetric(matchMetrics.f1, 'F1-Score')}
					</div>
			</div>
			<div className='match-predictions-nav'>
				<input
          type='text'
          className='search-bar'
          placeholder='Search items...'
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
				<select value={filterType} onChange={selectFilter}>
					<option value={1}>All</option>
					<option value={3}>Big Matches</option>
					<option value={4}>Majors</option>
				</select>
			</div>
      <div className='full-prediction-table-container'>
				<table className='prediction-table'>
					<thead>
						<tr className='prediction-table-header'>
							<th className='prediction-table-team'>Team A</th>
							<th className='prediction-table-team'>Team B</th>
							<th className='prediction-table-date'>Date</th>
							<th className='prediction-table-best-of'>Best Of</th>
							<th className='prediction-table-relavance'>Relavance</th>
							<th className='prediction-table-tournament'>Tournament</th>
							<th className='prediction-table-outcome'>Prediction</th>
							<th className='prediction-table-con'>Confidence</th>
							<th className='prediction-table-actoutcome'>Result</th>
						</tr>
					</thead>
					<tbody className='prediction-table-body'>
						{finalFilteredMatches.map((match, index) => (
							match.model_id === model.model_id || match.model_id === null ? (
								<tr key={match.match_id}>
									<td className={`prediction-table-team ${match.actual_outcome != null ? match.actual_outcome == 1 ? "winner" : "loser" : ""}`}>{match.team_a}</td>
									<td className={`prediction-table-team ${match.actual_outcome != null ? match.actual_outcome == 0 ? "winner" : "loser" : ""}`}>{match.team_b}</td>
									<td className='prediction-table-team'>{getDate(match.date)}</td>
									<td>{match.best_of}</td>
									<td>{match.tournament_type}</td>
									<td>{match.tournament_name}</td>
									<td>{match.prediction != null ? (match.prediction === 1 ? (match.team_a) : (match.team_b)) : "N/A"}</td>
									<td>{match.confidence ? match.confidence.toFixed(3) : "N/A"}</td>
									<td>{match.actual_outcome != null ? (match.actual_outcome === 1 ? (match.team_a) : (match.team_b)) : "N/A"}</td>
								</tr>) : (<></>)
							))}
					</tbody>
				</table>
			</div>
    </div>
  );
};

export default MatchPredictions;