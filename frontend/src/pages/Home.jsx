import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import RecentPredictions from '../components/RecentPredictions';
import ModelPerformance from '../components/ModelPerformance';
import DatasetInfo from '../components/DatasetInfo';
import './Home.css'

const Home = () => {
	const [pageName, setPageName] = useState("Model Overview")
	const [selectedModel, setSelectedModel] = useState("logistic_regression")

	return (
		<div className='Home'>
				<Navigation/>
				<div className='home-container'>
					<div className='home-body-container'>
						<ModelPerformance model={selectedModel}/>
						<DatasetInfo model={selectedModel}/>
						<RecentPredictions model={selectedModel}/>
					</div>
					
					
				</div>
		</div>
	)
}

export default Home;