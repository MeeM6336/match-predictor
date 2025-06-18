import React, { useState, useEffect, useMemo } from 'react';
import './DatasetInfo.css';
import { fetchTrainingDatasetStats, fetchLiveDatasetStats, fetchFeatureVectors} from '../assets/util/matches.js'

const DatasetInfo = ({model}) => {
  const [trainingDatasetStats, setTrainingDatasetStats] = useState({});
  const [liveDatasetStats, setLiveDatasetStats] = useState({});
  const [featureVectors, setFeatureVectors] = useState([]);
  const [selectedFeature, setSelectedFeature] = useState("ADR_diff");
  const [correlationMatrix, setCorrelationMatrix] = useState({});

  const selectFeature = (event) => {
    setSelectedFeature(event.target.value);
  };

  const getDate = (dateString) => {
		const date = new Date(dateString);

		const localString = date.toLocaleString('en-US', {
			timeZone: 'America/Chicago',
			year: '2-digit',
			month: '2-digit',
			day: '2-digit',
			hour12: false,
		});

		return localString
	};

  const getMatrixCellStyle = (value) => {
    const maxVal = 1
    const intensity = Math.abs(Math.round((value / maxVal) * 255));

    return {
      backgroundColor: `rgb(${intensity}, 0, ${255 - intensity})`,
      color: "white",
      width: "14rem",
      textAlign: 'center'
    };
  };

  useEffect(() => {
    const loadDatasetStats = async () => {
      let stats = await fetchTrainingDatasetStats(model.model_id);
      setTrainingDatasetStats(stats);
      stats = await fetchLiveDatasetStats(model.model_id);
      setLiveDatasetStats(stats)
    };

    const loadFeatureVectors = async () => {
      const fvArray = await fetchFeatureVectors(model.model_id);
      setFeatureVectors(fvArray);
    };

    const loadMatrix = async () => {
      try {
        const response = await fetch(`/data/${model.model_name}_Live_spearman_corr_matrix.json`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        };
        const data = await response.json();
        setCorrelationMatrix(data);
      } catch (err) {
        console.error("Failed to fetch correlation matrix:", err);
        setError(err);
      };
    };

    loadMatrix();
    loadDatasetStats();
    loadFeatureVectors();
  }, [model?.model_id]);

  const computedDistribution = useMemo(() => {
    if (!featureVectors || featureVectors.length == 0) 
      return {};

    const keys = Object.keys(featureVectors[0]);
    const stats = {};

    for (const key of keys) {
      const numericValues = featureVectors.map(fv => fv[key]).filter(val => typeof val === 'number' && val != null && !isNaN(val));

      if (numericValues.length === 0) {
        continue;
    }

      const mean = numericValues.reduce((a, b) => a + b, 0) / numericValues.length;
      const variance = numericValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / numericValues.length;
      const sd = Math.sqrt(variance);

      const sorted = [...numericValues].sort((a, b) => a - b);
      const mid = Math.floor(sorted.length / 2);
      const median = sorted.length % 2 === 0
        ? (sorted[mid - 1] + sorted[mid]) / 2
        : sorted[mid];
      stats[key] = { mean, sd, median };
    };
    return stats;
  }, [featureVectors]);

  return (
    <div className='DatasetInfo'>
      <div className='data-info-header'>
        <p>Dataset Information</p>
      </div>
      <div className='data-info-body'>
        <div className='data-info-body-column'>
          {Object.keys(trainingDatasetStats).length > 0 ? (
            <div className='dataset-overview-container'>
              <div className='dataset-overview-header'>
                <p>Training Dataset Overview</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Match Count:</p>
                <p>{trainingDatasetStats.match_row_count}</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Feature Vectors:</p>
                <p>{trainingDatasetStats.feature_row_count}</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Features Count:</p>
                <p>{trainingDatasetStats.feature_count}</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Date Range:</p>
                <p>{getDate(trainingDatasetStats.match_min_date)} - {getDate(trainingDatasetStats.match_max_date)}</p>
              </div>
            </div>
          ) : (<></>)}
          {Object.keys(liveDatasetStats).length > 0 ? (
            <div className='dataset-overview-container'>
              <div className='dataset-overview-header'>
                <p>Live Dataset Overview</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Match Count:</p>
                <p>{liveDatasetStats.match_row_count}</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Feature Vectors:</p>
                <p>{liveDatasetStats.feature_row_count}</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Features Count:</p>
                <p>{liveDatasetStats.feature_count}</p>
              </div>
              <div className='dataset-overview-item'>
                <p className='dataset-overview-type'>Date Range:</p>
                <p>{getDate(liveDatasetStats.match_min_date)} - {getDate(liveDatasetStats.match_max_date)}</p>
              </div>
            </div>
          ) : (<></>)}
          <div className='dataset-feature-correlation-matrix-container'>
            <p className='dataset-feature-correlation-header'>Feature Correlation Matrix</p>
            <div className='dataset-table-container'>
              <table className='dataset-feature-correlation-matrix'>
                <thead>
                  <tr>
                    <th></th>
                    {Object.keys(correlationMatrix).length > 0 ? (
                      Object.keys(correlationMatrix).map(feature => (
                      <th className='feature-column' key={feature}>{feature}</th>
                    ))) : (<></>)}
                  </tr>
                </thead>
                <tbody>
                  {Object.keys(correlationMatrix).map(rowFeature => (
                    <tr key={rowFeature}>
                      <td className='feature-row'>{rowFeature}</td>
                      {Object.keys(correlationMatrix).map(colFeature => (
                        <td key={colFeature} style={getMatrixCellStyle(correlationMatrix[rowFeature][colFeature])}>
                          {correlationMatrix[rowFeature][colFeature] !== undefined
                            ? correlationMatrix[rowFeature][colFeature].toFixed(2) : ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className='correlation-matrix-legend'></div>
            </div>
          </div>
        </div>
        <div className='data-info-body-column'>
          <div className='dataset-distribution-container'>
            <div className='dataset-distribution-header'>
              <p>Live Feature Distribution</p>
              <select className='dataset-distribution-select' value={selectedFeature} onChange={selectFeature}>
                {Object.keys(computedDistribution).map(feature => {
                  if (computedDistribution[feature] != 0) {
                    return <option value={feature}>{feature}</option>
                  }
                  return null;
                }
                )}
              </select>
            </div>
            <div className='dataset-overview-item'>
              <p className='dataset-overview-type'>Mean:</p>
              <p>{computedDistribution?.[selectedFeature]?.mean?.toFixed(4)}</p>
            </div>
            <div className='dataset-overview-item'>
              <p className='dataset-overview-type'>Standard Deviation:</p>
              <p>{computedDistribution?.[selectedFeature]?.sd?.toFixed(4)}</p>
            </div>
            <div className='dataset-overview-item'>
              <p className='dataset-overview-type'>Median:</p>
              <p>{computedDistribution?.[selectedFeature]?.median?.toFixed(4)}</p>
            </div>
            <p className='dataset-distribution-image-header'>Rolling Statistics for {selectedFeature}</p>
            {model ? (
              <img src={`/images/${model.model_name}_Live_rolling_stats_${selectedFeature}.png`}/>
            ) : (<></>)}
          </div>
          <div className='data-insertion-container'>
            <p>Live Matches Insertion by Day</p>
            <img src='/images/Live_match_insertions.png'/>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatasetInfo;