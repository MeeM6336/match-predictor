import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import RecentPredictions from '../components/RecentPredictions';
import ModelPerformance from '../components/ModelPerformance';
import DatasetInfo from '../components/DatasetInfo';
import MatchPredictions from '../components/MatchPredictions';
import './Home.css'

const Home = () => {
	const [pageName, setPageName] = useState("Model Overview")
	const [selectedModel, setSelectedModel] = useState({model_name: "logistic_regression", model_id: 1})

	const handleModelChange = (newModel) => {
    setSelectedModel(newModel);
  };

	const handlePageChange = (newPage) => {
		setPageName(newPage)
	};

	const renderPage = () => {
		if(pageName === "Model Overview") {
			return (
				<div className='home-body-container'>
					<ModelPerformance model={selectedModel}/>
					<DatasetInfo model={selectedModel}/>
					<RecentPredictions model={selectedModel} onPageChange={handlePageChange}/>
				</div>
			)
		}
		else if (pageName === "Match Predictions") {
			return (
				<div>
					<MatchPredictions model={selectedModel}/>
				</div>
			)
		}
	}

	return (
		<div className='Home'>
			<Navigation onModelChange={handleModelChange} onPageChange={handlePageChange}/>
			<div className='home-container'>
				{renderPage()}
			</div>
		</div>
	)
}

export default Home;