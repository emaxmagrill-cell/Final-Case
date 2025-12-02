// Fantasy Football Leaderboard - JavaScript Frontend

const API_BASE = '/api';
let currentLeaderboard = null;
let currentMetadata = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Populate seasons dropdown
    fetchSeasons();
    
    // Set up event listeners
    document.getElementById('load-btn').addEventListener('click', loadData);
    document.getElementById('download-btn').addEventListener('click', downloadCSV);
    document.getElementById('scoring-toggle').addEventListener('click', toggleScoringRules);
    document.getElementById('top-n').addEventListener('input', updateTopNValue);
    
    // Populate weeks
    populateWeeks();
    
    // Fetch scoring rules
    fetchScoringRules();
}

function fetchSeasons() {
    fetch(`${API_BASE}/seasons`)
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('season-select');
            select.innerHTML = '';
            data.seasons.forEach(season => {
                const option = document.createElement('option');
                option.value = season;
                option.textContent = season;
                if (season === data.current) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        })
        .catch(error => showError('Failed to load seasons'));
}

function populateWeeks() {
    const select = document.getElementById('week-select');
    for (let i = 1; i <= 18; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `Week ${i}`;
        select.appendChild(option);
    }
}

function updateTopNValue() {
    const value = document.getElementById('top-n').value;
    document.getElementById('top-n-value').textContent = value;
}

function loadData() {
    const season = document.getElementById('season-select').value;
    const week = document.getElementById('week-select').value || null;
    const topN = document.getElementById('top-n').value;
    const positions = Array.from(document.querySelectorAll('.checkbox-group input:checked'))
        .map(cb => cb.value)
        .join(',');
    
    showLoading();
    
    const params = new URLSearchParams({
        season: season,
        top_n: topN,
        ...(week && { week: week }),
        ...(positions && { position: positions })
    });
    
    fetch(`${API_BASE}/leaderboard?${params}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to load data');
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            
            currentLeaderboard = data.leaderboard;
            currentMetadata = data.metadata;
            
            updateMetrics();
            populateLeaderboard();
            generateCharts();
            
            document.getElementById('season-display').textContent = season;
            document.getElementById('download-btn').disabled = false;
            
            hideLoading();
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to load leaderboard data. Please try again.');
            hideLoading();
        });
}

function updateMetrics() {
    if (!currentMetadata) return;
    
    const metricCards = document.querySelectorAll('.metric-card');
    
    metricCards[0].querySelector('.metric-value').textContent = currentMetadata.total_players;
    metricCards[0].querySelector('.metric-label').textContent = 'Total Players';
    
    metricCards[1].querySelector('.metric-value').textContent = currentMetadata.top_score.toFixed(1);
    metricCards[1].querySelector('.metric-label').textContent = 'Top Score';
    
    metricCards[2].querySelector('.metric-value').textContent = currentMetadata.average_score.toFixed(1);
    metricCards[2].querySelector('.metric-label').textContent = 'Average Score';
    
    metricCards[3].querySelector('.metric-label').textContent = 'Season';
    // Keep existing season display
}

function populateLeaderboard() {
    if (!currentLeaderboard || currentLeaderboard.length === 0) {
        showError('No players to display');
        return;
    }
    
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';
    
    currentLeaderboard.forEach((player, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${player.player_name || '-'}</td>
            <td>${player.position || '-'}</td>
            <td><strong>${player.fantasy_points.toFixed(1)}</strong></td>
            <td>${player.pass_td || 0}</td>
            <td>${player.pass_yards ? player.pass_yards.toFixed(0) : 0}</td>
            <td>${player.rush_td || 0}</td>
            <td>${player.rush_yards ? player.rush_yards.toFixed(0) : 0}</td>
            <td>${player.rec_td || 0}</td>
            <td>${player.rec_yards ? player.rec_yards.toFixed(0) : 0}</td>
            <td>${player.reception || 0}</td>
        `;
        tbody.appendChild(row);
    });
    
    document.getElementById('leaderboard-container').classList.remove('hidden');
    document.getElementById('charts-container').classList.remove('hidden');
}

function generateCharts() {
    if (!currentLeaderboard || currentLeaderboard.length === 0) return;
    
    // Top 10 Bar Chart
    const top10 = currentLeaderboard.slice(0, 10);
    const names = top10.map(p => p.player_name);
    const points = top10.map(p => p.fantasy_points);
    
    const barTrace = {
        x: points,
        y: names,
        type: 'bar',
        orientation: 'h',
        marker: {
            color: points.map((p, i) => `rgba(31, 119, 210, ${0.5 + (i / 10) * 0.5})`)
        }
    };
    
    const barLayout = {
        margin: { l: 150, r: 50, t: 20, b: 50 },
        xaxis: { title: 'Fantasy Points' },
        height: 400,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(240,242,246,0.5)'
    };
    
    Plotly.newPlot('chart-top-10', [barTrace], barLayout, { responsive: true });
    
    // Distribution Histogram
    const histTrace = {
        x: currentLeaderboard.map(p => p.fantasy_points),
        type: 'histogram',
        nbinsx: 30,
        marker: { color: 'rgba(31, 119, 210, 0.7)' }
    };
    
    const histLayout = {
        margin: { l: 50, r: 50, t: 20, b: 50 },
        xaxis: { title: 'Fantasy Points' },
        yaxis: { title: 'Number of Players' },
        height: 400,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(240,242,246,0.5)'
    };
    
    Plotly.newPlot('chart-distribution', [histTrace], histLayout, { responsive: true });
}

function downloadCSV() {
    const season = document.getElementById('season-select').value;
    const week = document.getElementById('week-select').value || null;
    
    const params = new URLSearchParams({
        season: season,
        ...(week && { week: week })
    });
    
    window.location.href = `${API_BASE}/download-csv?${params}`;
}

function fetchScoringRules() {
    fetch(`${API_BASE}/scoring`)
        .then(response => response.json())
        .then(data => {
            const rulesDiv = document.getElementById('scoring-rules');
            rulesDiv.innerHTML = '';
            
            Object.entries(data.rules).forEach(([stat, points]) => {
                const rule = document.createElement('div');
                rule.className = 'scoring-rule';
                rule.innerHTML = `
                    <span>${stat.replace(/_/g, ' ').toUpperCase()}</span>
                    <strong>${points} pts</strong>
                `;
                rulesDiv.appendChild(rule);
            });
        })
        .catch(error => console.error('Error loading scoring rules:', error));
}

function toggleScoringRules() {
    document.getElementById('scoring-rules').classList.toggle('hidden');
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('error').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = '❌ ' + message;
    errorDiv.classList.remove('hidden');
    document.getElementById('leaderboard-container').classList.add('hidden');
    document.getElementById('charts-container').classList.add('hidden');
    hideLoading();
}
