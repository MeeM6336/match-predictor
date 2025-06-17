import React, { useState, useEffect } from 'react';
import './RecentPredictions.css';
import { fetchUpcomingMatches } from '../assets/util/matches';

const RecentPredictions = ({model, onPageChange}) => {
	const [upcomingMatchList, setUpcomingMatchList] = useState([]);

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

	const selectPage = (pageName) => {
		onPageChange(pageName);
	};

	useEffect(() => {
		const loadMatches = async () => {
			const matches = await fetchUpcomingMatches(model.model_id);
			setUpcomingMatchList(matches.slice(0, 40));
		};

		loadMatches();
	}, [model?.model_id]);

	return (
		<div className='RecentPredictions'>
			<div className='prediction-header'>
				<p>Recent Predictions</p>
				<a onClick={() => selectPage("Match Predictions")}>See More &gt;</a>
			</div>
			<div className='prediction-table-container'>
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
						{upcomingMatchList.map((match, index) => (
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

export default RecentPredictions;