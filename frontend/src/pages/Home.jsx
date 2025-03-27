import React, { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import './Home.css'

const Home = () => {

    return (
        <div className='Home'>
            <Navigation/>
            <div className='home-container'>
                <p>Overview</p>
            </div>
        </div>
    )
}

export default Home