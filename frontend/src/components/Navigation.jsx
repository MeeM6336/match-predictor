import React, { useState, useEffect } from 'react';
import './Navigation.css'
import logo from '../assets/images/nav_logo.png'
import settings_icon from '../assets/images/settings_icon.png'
import dashboard_icon from '../assets/images/dashboard_icon.png'
import predicitons_icon from '../assets/images/predictions_icon.png'
import features_icon from '../assets/images/features_icon.png'

const Navigation = () => {

	return (
		<div className='Navigation'>
			<div className='nav-overview-container'>
				<img src={logo}/>
				<p>FragForecast</p>    
			</div>
			<div className='nav-links-container'>
				<ul className='nav-links'>
					<li>
							<button className='nav-links-button'>
								<img src={dashboard_icon}/>
								Model Overview</button>
					</li>
					<li>
							<button className='nav-links-button'>
								<img src={predicitons_icon}/>
								Match Predictions
							</button>
					</li>
					<li>
							<button className='nav-links-button'>
								<img src={features_icon}/>
								Feature Insights</button>
					</li>
					<li>
							<button className='nav-links-button'>
									<img src={settings_icon}/>
									Settings
							</button>
					</li>
				</ul>
			</div>
		</div>
	)
}

export default Navigation;