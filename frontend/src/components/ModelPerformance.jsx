import React, { useState, useEffect } from 'react';
import './ModelPerformance.css';
import { fetchModelMetrics, fetchMatchPredictionStats } from '../assets/util/matches';


const ModelPerformance = () => {
  
  const [modelMetric, setModelMetric] = useState();
  const [upcomingMatchStats, setUpcomingMatchStats] = useState();
  const [calculatedMetrics, setCalculatedMetrics] = useState();

  useEffect(() => {
    const loadModelMetric = async () => {
      const metric = await fetchModelMetrics("logistic regression", "2025-04-14 09:23:00");
      setModelMetric(metric[0]);
    };

    loadModelMetric();
  }, []);

  useEffect (() => {
    const loadUpcomingMatchStats = async () => {
      const upcomingMatchStats = await fetchMatchPredictionStats();
      setUpcomingMatchStats(upcomingMatchStats[0]);
      console.log(upcomingMatchStats);
    }

    loadUpcomingMatchStats();
  }, []);

  useEffect(() => {
    if(!modelMetric)
      return;

    const calculateMetrics = () => {
      const calculateLogLoss = (yTrue, yPred) => {
        const epsilon = 1e-15;
        let totalLoss = 0;
      
        for (let i = 0; i < yTrue.length; i++) {
          const y = yTrue[i];
          let p = yPred[i];
      
          p = Math.min(Math.max(p, epsilon), 1 - epsilon);
      
          const loss = -(y * Math.log(p) + (1 - y) * Math.log(1 - p));
          totalLoss += loss;
        }
      
        return totalLoss / yTrue.length;
      };

      const accuracy = (modelMetric.t_pos + modelMetric.t_neg)/(modelMetric.t_pos + modelMetric.t_neg + modelMetric.f_neg + modelMetric.f_pos);
      const precision = (modelMetric.t_pos)/(modelMetric.t_pos + modelMetric.f_pos);
      const recall = (modelMetric.t_pos)/(modelMetric.t_pos + modelMetric.f_neg);
      const f1 = (2 * precision * recall)/(precision + recall); 
      const logLoss = calculateLogLoss(modelMetric.)

      setCalculatedMetrics([accuracy, precision, recall, f1])
    };

    calculateMetrics();
  }, [modelMetric, upcomingMatchStats])

  const getMatrixCellStyle = (value) => {
    const maxVal = modelMetric['t_neg'] + modelMetric['t_pos'] + modelMetric['f_neg'] + modelMetric['f_pos'];
    
    const intensity = Math.round((value / maxVal) * 255);

    return {
      backgroundColor: `rgb(${intensity}, 0, ${255 - intensity})`,
      color: "white",
      padding: "1rem",
      paddingLeft: "3rem",
      paddingRight: "3rem"
    };
  };

  return (
    <div className='ModelPerformance'>
      <div className='performance-header'>
        <p>Model Performance</p>
      </div>
      {calculatedMetrics ? (
        <div className='performance-metrics-container'>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[0]).toFixed(4)}</p>
            <p className='performance-metric-name'>Accuracy</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[1]).toFixed(4)}</p>
            <p className='performance-metric-name'>Precision</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[2]).toFixed(4)}</p>
            <p className='performance-metric-name'>Recall</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[3]).toFixed(4)}</p>
            <p className='performance-metric-name'>F1-Score</p>
          </div>
        </div>
      ) : (<div></div>)}
        <div className='performance-grid-container'>
          <div className='confusion-matrix-container'>
            <p>Training Data Confusion Matrix</p>
              <div className='confusion-matrix-table-container'>
                <table className='confusion-matrix-table'>
                  <thead>
                    <tr>
                      <th></th>
                      <th>0</th>
                      <th>1</th>
                    </tr>
                  </thead>
                  {modelMetric ? (
                    <tbody>
                      <tr>
                        <th>0</th>
                        <td style={getMatrixCellStyle(modelMetric.t_neg)}>{modelMetric.t_neg}</td>
                        <td style={getMatrixCellStyle(modelMetric.f_pos)}>{modelMetric.f_pos}</td>
                      </tr>
                      <tr>
                        <th>1</th>
                        <td style={getMatrixCellStyle(modelMetric.f_neg)}>{modelMetric.f_neg}</td>
                        <td style={getMatrixCellStyle(modelMetric.t_pos)}>{modelMetric.t_pos}</td>
                      </tr>
                    </tbody>
                    ) : (<tbody></tbody>)}
                </table>
              <div className='confusion-matrix-legend'></div>
          </div>
        </div>
        <div className='prediction-container'>
          <p></p>
        </div>
        <div className='accuracy-history-container'>
          
        </div>
      </div>
    </div>
  );
};

export default ModelPerformance