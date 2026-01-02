// Application JavaScript pour l'interface web

let currentSection = 'dashboard';
let paysData = null;
let typesRisques = [];
let toutesCrises = [];

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadStockInputs();
    loadTypesRisques();
});

// Navigation entre sections
function showSection(section) {
    document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
    document.getElementById(section + '-section').style.display = 'block';
    currentSection = section;
    
    // Charge les données selon la section
    if (section === 'dashboard') {
        loadDashboard();
    } else if (section === 'crises') {
        loadCrises();
    }
}

// Charge le tableau de bord
async function loadDashboard() {
    try {
        const response = await fetch('/api/statistiques');
        const result = await response.json();
        
        if (result.success) {
            const stats = result.data;
            document.getElementById('stat-total-crises').textContent = stats.total_crises;
            document.getElementById('stat-crises-actuelles').textContent = stats.crises_actuelles || 0;
            document.getElementById('stat-intensite-moy').textContent = stats.intensite_moyenne.toFixed(2);
            document.getElementById('stat-population').textContent = (stats.population_totale / 1000000).toFixed(1) + 'M';
            
            // Graphique
            const ctx = document.getElementById('chart-types');
            if (ctx) {
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(stats.par_type),
                        datasets: [{
                            data: Object.values(stats.par_type),
                            backgroundColor: [
                                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                                '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
                                '#4BC0C0', '#FF6384', '#36A2EB'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Charge les crises
async function loadCrises() {
    try {
        const seulementActuelles = document.getElementById('filter-actuelles').checked;
        const response = await fetch(`/api/crises?actuelles=${seulementActuelles}`);
        const result = await response.json();
        
        if (result.success) {
            toutesCrises = result.data;
            afficherCrises(toutesCrises);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Affiche les crises dans le tableau
function afficherCrises(crises) {
    const tbody = document.querySelector('#table-crises tbody');
    tbody.innerHTML = '';
    
    crises.forEach(crise => {
        const row = tbody.insertRow();
        const enCours = crise.en_cours ? '<span class="badge bg-danger">Actuelle</span>' : '<span class="badge bg-secondary">Passée</span>';
        row.innerHTML = `
            <td>${crise.nom_crise}</td>
            <td><span class="badge bg-primary">${crise.type_crise}</span></td>
            <td>${crise.pays}</td>
            <td>${new Date(crise.date).toLocaleDateString('fr-FR')}</td>
            <td><span class="badge bg-danger">${crise.intensite}</span></td>
            <td>${crise.population_touchee.toLocaleString('fr-FR')}</td>
            <td>${enCours}</td>
        `;
    });
}

// Filtre les crises
document.addEventListener('DOMContentLoaded', function() {
    const filterCheckbox = document.getElementById('filter-actuelles');
    if (filterCheckbox) {
        filterCheckbox.addEventListener('change', loadCrises);
    }
});

// Charge les inputs de stock
function loadStockInputs() {
    const ressources = [
        { key: 'eau_potable_litres', label: 'Eau potable (litres)', defaut: 50000000 },
        { key: 'tentes', label: 'Tentes', defaut: 10000 },
        { key: 'medicaments_doses', label: 'Médicaments (doses)', defaut: 500000 },
        { key: 'hopitaux_campagne', label: 'Hôpitaux de campagne', defaut: 100 },
        { key: 'generateurs', label: 'Générateurs', defaut: 300 },
        { key: 'vehicules_urgence', label: 'Véhicules d urgence', defaut: 200 },
        { key: 'personnel_medical', label: 'Personnel médical', defaut: 3000 },
        { key: 'denrees_alimentaires_kg', label: 'Denrées alimentaires (kg)', defaut: 10000000 }
    ];
    
    const container = document.getElementById('stock-inputs');
    container.innerHTML = '';
    
    ressources.forEach(ressource => {
        const col = document.createElement('div');
        col.className = 'col-md-6 mb-3';
        col.innerHTML = `
            <label class="form-label">${ressource.label}</label>
            <input type="number" class="form-control" id="stock-${ressource.key}" 
                   value="${ressource.defaut}" min="0">
        `;
        container.appendChild(col);
    });
}

// Calcule l'allocation
async function calculerAllocation() {
    const stock = {};
    document.querySelectorAll('[id^="stock-"]').forEach(input => {
        const key = input.id.replace('stock-', '');
        stock[key] = parseInt(input.value) || 0;
    });
    
    // Par défaut, on ne considère que les crises actuelles
    const seulementActuelles = true;
    
    try {
        const response = await fetch('/api/allocation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stock, seulement_actuelles: seulementActuelles })
        });
        
        const result = await response.json();
        
        if (result.success) {
            afficherResultatsAllocation(result);
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors du calcul');
    }
}

// Affiche les résultats d'allocation
function afficherResultatsAllocation(result) {
    const container = document.getElementById('allocation-results');
    container.style.display = 'block';
    
    let html = `
        <div class="alert alert-info alert-custom">
            <i class="fas fa-info-circle"></i> 
            <strong>${result.nb_crises_traitees} crise(s) ${result.seulement_actuelles ? 'actuelle(s)' : ''} traitée(s)</strong>
        </div>
    `;
    
    if (result.top5.length === 0) {
        html += '<div class="alert alert-warning">Aucune crise actuelle à traiter. Vérifiez que des crises sont marquées comme actuelles (en_cours=True).</div>';
    } else {
        html += '<div class="card"><div class="card-header"><i class="fas fa-trophy"></i> Top 5 Crises Prioritaires</div><div class="card-body"><ul class="list-group">';
        
        result.top5.forEach((crise, idx) => {
            html += `
                <li class="list-group-item">
                    <strong>${idx + 1}. ${crise.nom_crise}</strong> (${crise.type_crise})<br>
                    <small>Score d urgence: ${crise.score_urgence_normalise.toFixed(2)}%</small>
                </li>
            `;
        });
        
        html += '</ul></div></div>';
        
        html += '<div class="card mt-3"><div class="card-header"><i class="fas fa-boxes"></i> Stocks Restants</div><div class="card-body"><ul class="list-group">';
        
        for (const [ressource, quantite] of Object.entries(result.stock_restant)) {
            html += `<li class="list-group-item">${ressource.replace(/_/g, ' ')}: ${quantite.toLocaleString('fr-FR')}</li>`;
        }
        
        html += '</ul></div></div>';
    }
    
    container.innerHTML = html;
}

// Génère la carte
async function genererCarte() {
    const includeAllocation = document.getElementById('include-allocation').checked;
    
    try {
        const response = await fetch(`/api/carte?allocation=${includeAllocation}`);
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('carte-container');
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> Carte générée avec succès!
                    <a href="${result.url}" target="_blank" class="btn btn-primary btn-sm ms-2">
                        <i class="fas fa-external-link-alt"></i> Ouvrir la carte
                    </a>
                </div>
                <iframe src="${result.url}" width="100%" height="600" style="border: none; border-radius: 10px;"></iframe>
            `;
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la génération');
    }
}

// Charge les types de risques
async function loadTypesRisques() {
    try {
        const response = await fetch('/api/types-risques');
        const result = await response.json();
        
        if (result.success) {
            typesRisques = result.data;
            const select = document.getElementById('type-risque');
            select.innerHTML = '<option value="">Sélectionnez un type...</option>';
            typesRisques.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Recherche un pays
async function rechercherPays() {
    const nomPays = document.getElementById('pays-input').value.trim();
    
    if (!nomPays) {
        alert('Veuillez entrer un nom de pays');
        return;
    }
    
    try {
        const response = await fetch(`/api/pays?nom=${encodeURIComponent(nomPays)}`);
        const result = await response.json();
        
        if (result.success) {
            paysData = result.data;
            const container = document.getElementById('pays-info');
            container.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h5><i class="fas fa-flag"></i> ${paysData.pays}</h5>
                        <p><strong>Latitude:</strong> ${paysData.latitude}</p>
                        <p><strong>Longitude:</strong> ${paysData.longitude}</p>
                        <p><strong>Population:</strong> ${paysData.population.toLocaleString('fr-FR')} habitants</p>
                    </div>
                </div>
            `;
            document.getElementById('prediction-form').style.display = 'block';
        } else {
            alert('Pays non trouvé: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la recherche');
    }
}

// Calcule la prédiction
async function calculerPrediction() {
    if (!paysData) {
        alert('Veuillez d abord rechercher un pays');
        return;
    }
    
    const typeRisque = document.getElementById('type-risque').value;
    const intensite = parseFloat(document.getElementById('intensite').value);
    const budget = parseFloat(document.getElementById('budget').value);
    
    if (!typeRisque) {
        alert('Veuillez sélectionner un type de risque');
        return;
    }
    
    try {
        const response = await fetch('/api/prediction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pays: paysData.pays,
                type_risque: typeRisque,
                intensite: intensite,
                budget: budget
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            afficherResultatsPrediction(result);
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors du calcul');
    }
}

// Affiche les résultats de prédiction
function afficherResultatsPrediction(result) {
    const container = document.getElementById('prediction-results');
    
    let html = `
        <div class="card mt-3">
            <div class="card-header bg-info text-white">
                <i class="fas fa-chart-line"></i> Probabilité de l Événement
            </div>
            <div class="card-body">
                <h3>${result.probabilite.probabilite}%</h3>
                <p><strong>Niveau:</strong> <span class="badge bg-warning">${result.probabilite.niveau}</span></p>
                <p><small>${result.probabilite.explication}</small></p>
            </div>
        </div>
        
        <div class="card mt-3">
            <div class="card-header bg-success text-white">
                <i class="fas fa-euro-sign"></i> Besoins en Ressources
            </div>
            <div class="card-body">
                <div class="row">
    `;
    
    result.ressources.forEach(ressource => {
        const pourcentage = result.pourcentage_total > 100 ? 
            (ressource.pourcentage * 100 / result.pourcentage_total) : ressource.pourcentage;
        
        html += `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h6>${ressource.nom}</h6>
                        <p><strong>Quantité:</strong> ${ressource.quantite.toLocaleString('fr-FR')}</p>
                        <p><strong>Coût:</strong> ${ressource.cout.toLocaleString('fr-FR')} €</p>
                        <div class="progress progress-custom">
                            <div class="progress-bar" role="progressbar" 
                                 style="width: ${Math.min(pourcentage, 100)}%">
                                ${ressource.pourcentage.toFixed(2)}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
                </div>
                <hr>
                <div class="alert ${result.pourcentage_total > 100 ? 'alert-danger' : 'alert-success'}">
                    <h5>Coût Total: ${result.cout_total.toLocaleString('fr-FR')} €</h5>
                    <h5>Pourcentage du Budget: ${result.pourcentage_total.toFixed(2)}%</h5>
                    ${result.pourcentage_total > 100 ? 
                        '<p class="mb-0">⚠ Budget insuffisant! Déficit: ' + 
                        (result.cout_total - result.budget).toLocaleString('fr-FR') + ' €</p>' :
                        '<p class="mb-0">✓ Budget suffisant. Reste: ' + 
                        (result.budget - result.cout_total).toLocaleString('fr-FR') + ' €</p>'
                    }
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

