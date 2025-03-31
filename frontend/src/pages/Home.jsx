import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import './Home.css'

const Home = () => {

	const [recentPredictions, setRecentPredictions] = useState([])

	return (
		<div className='Home'>
				<Navigation/>
				<div className='home-container'>
					<div className='home-header-container'>
						<p className='home-header-title'>Model Name</p>
						<p className='home-header-subtitle'>A CS2 Profesional Match Outcome Learning Model</p>
						<p className='home-header-subtitle'>Model Ver 0.00</p>
					</div>
					<div className='home-body-container'>
						<div className='home-recent-predictions'>
							<p>Recent Predictions</p>
							{recentPredictions.map((prediction) => (
								<div className='prediction'>
									<p></p>
								</div>
							))}
						</div>
						<div className='home-model-performance'>
							<p>Model Performance</p>
						</div>
						<div className='home-dataset-info'>
							<p>Dataset Information</p>
						</div>
					</div>
				</div>
		</div>
	)
}

export default Home;