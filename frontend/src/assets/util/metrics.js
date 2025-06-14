export function computeRocAuc(y_true, y_prob) {
  const data = y_true.map((label, idx) => ({ label, prob: y_prob[idx] }));

  data.sort((a, b) => b.prob - a.prob);

  let tp = 0;
  let fp = 0;
  const tps = [];
  const fps = [];

  const P = y_true.filter(y => y === 1).length;
  const N = y_true.filter(y => y === 0).length;

  for (const point of data) {
    if (point.label === 1) {
      tp++;
    } else {
      fp++;
    }
    tps.push(tp);
    fps.push(fp);
  };

  const tpr = tps.map(v => v / P);
  const fpr = fps.map(v => v / N);

  let auc = 0;
  for (let i = 1; i < tpr.length; i++) {
    const width = fpr[i] - fpr[i - 1];
    const height = (tpr[i] + tpr[i - 1]) / 2;
    auc += width * height;
  };

  return auc;
};

export function computeLogLoss(y_true, y_prob) {
  const eps = 1e-15;
  let loss = 0;
  
  for (let i = 0; i < y_true.length; i++) {
    const y = y_true[i];
    const p = Math.min(Math.max(y_prob[i], eps), 1 - eps);
    loss += y * Math.log(p) + (1 - y) * Math.log(1 - p);
  }
  return -loss / y_true.length;
};