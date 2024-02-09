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

async function generateUserStatsPieChart() {
    var ctx = document.getElementById('user-chart').getContext('2d');
    _labels = JSON.parse(await sendJsonRequest('/api/users_stats'));
    var chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(_labels),
            datasets: [{
                label: 'Pie Chart',
                data: Object.values(_labels),
                backgroundColor: ['#990011', '#FFA351', '#2BAE66', '#D9E5D6'],
            }]
        },
        options: {
            title: {
                display: true,
                text: 'User Stats'
            },
            labelsPosition: 'outside',
            plugins: {
                datalabels: {
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }
                
            }
        }
    });

    chart.canvas.parentNode.style.width = '250px';
    chart.canvas.parentNode.style.height = '250px';
    chart.canvas.parentNode.style.margin = '0 auto';
}

async function generateEventsStatsPieChart(id) {
    var ctx = document.getElementById('events-chart').getContext('2d');
    _labels = JSON.parse(await sendJsonRequest(`/api/events_stats/${id}`));
    var chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(_labels),
            datasets: [{
                label: 'Pie Chart',
                data: Object.values(_labels),
                backgroundColor: ['#990011', '#FFA351', '#2BAE66', '#D9E5D6'],
            }]
        },
        options: {
            title: {
                display: true,
                text: 'Events Stats'
            },
            labelsPosition: 'outside',
            plugins: {
                datalabels: {
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }
            }
        }
    });

    chart.canvas.parentNode.style.width = '250px';
    chart.canvas.parentNode.style.height = '250px';
    chart.canvas.parentNode.style.margin = '0 auto';
}