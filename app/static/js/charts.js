async function fetchJsonResponse(url, options) {
    console.log('fetchJsonResponse', url, options)
    const response = await fetch(url, options);
  
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  
    return await response.json();
  }

async function sendJsonRequest(url, method = 'GET', data = null) {
    try {
      const headers = {
        'Content-Type': 'application/json'
      };
  
      const options = {
        method: method,
        headers: headers,
        credentials: 'same-origin'
      };
  
      if (data) {
        options.body = JSON.stringify(data);
      }
  
      const response = await fetchJsonResponse(url, options);
  
      return response;
    } catch (error) {
      console.error('Error:', error);
      throw error;
    }
}

async function generateTopChattersChart() {
    var ctx = document.getElementById('chatters-histogram').getContext('2d');
    _labels = JSON.parse(await sendJsonRequest('/api/chatters_stats'));
    var chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(_labels),
            datasets: [{
                label: 'Users',
                data: Object.values(_labels),
                backgroundColor: ['#990011', '#FFA351', '#2BAE66', '#D9E5D6', '#FFC0CB'],
            }]
        },
        options: {
            title: {
                display: true,
                text: 'Top 5 Chatters'
            },
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: {
                datalabels: {
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }
            }
        }
    });

    chart.canvas.parentNode.style.height = '250px';
    chart.canvas.parentNode.style.margin = '0 auto';
}


async function generateChart(elementId, apiEndpoint, chartType, chartTitle) {
    var ctx = document.getElementById(elementId).getContext('2d');
    _labels = JSON.parse(await sendJsonRequest(apiEndpoint));

    // Map labels to colors
    var colors = {
        'Win': '#59a14f', // Soft green
        'Tie': '#FFEB3B', // Soft yellow
        'Loss': '#e15759' // Soft red
    };

    // Fallback colors
    var fallbackColors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f'];

    var chart = new Chart(ctx, {
        type: chartType,
        data: {
            labels: Object.keys(_labels),
            datasets: [{
                label: 'Users',
                data: Object.values(_labels),
                backgroundColor: Object.keys(_labels).map((key, index) => colors[key] || fallbackColors[index % fallbackColors.length]),
                borderColor: '#ffffff',
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: chartTitle,
                fontColor: '#333333',
                fontSize: 16
            },
            indexAxis: chartType === 'bar' ? 'y' : undefined,
            maintainAspectRatio: false,
            plugins: {
                datalabels: {
                    color: '#333333',
                    font: {
                        size: 14
                    },
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }
            }
        }
    });

    chart.canvas.parentNode.style.width = '100%';
    chart.canvas.parentNode.style.height = 'auto';
    chart.canvas.parentNode.style.margin = '0 auto';
}