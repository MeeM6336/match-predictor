import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import RecentPredictions from '../components/RecentPredictions';
import ModelPerformance from '../components/ModelPerformance';
import './Home.css'

const Home = () => {

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
						<RecentPredictions/>
						<ModelPerformance/>
						<div className='home-dataset-info'>
							<p>Dataset Information</p>
						</div>
					</div>
				</div>
		</div>
	)
}

export default Home;