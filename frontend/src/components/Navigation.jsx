import React, { useState, useEffect } from 'react';
import './Navigation.css'
import logo from '../assets/images/nav_logo.png'
import settings_icon from '../assets/images/settings_icon.png'

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
							<button className='nav-links-button'>Model Overview</button>
					</li>
					<li>
							<button className='nav-links-button'>Match Predictions</button>
					</li>
					<li>
							<button className='nav-links-button'>Feature Insights</button>
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