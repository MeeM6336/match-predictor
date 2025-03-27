import React, { useState, useEffect } from 'react';
import './Navigation.css'

const Navigation = () => {

    return (
        <div className='Navigation'>
            <div className='nav-links-container'>
                <ul className='nav-links'>
                    <li>
                        <button>Model Overview</button>
                    </li>
                    <li>
                        <button>Dataset</button>
                    </li>
                    <li>
                        <button>Settings</button>
                    </li>
                </ul>
            </div>
        </div>
    )
}

export default Navigation