// Application JavaScript pour l'interface web

let currentSection = 'dashboard';
let paysData = null;
let typesRisques = [];
let toutesCrises = [];
let typesCrisesDisponibles = [];

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
            // Extrait les types de crises uniques
            typesCrisesDisponibles = [...new Set(toutesCrises.map(c => c.type_crise))].sort();
            chargerTypesCrises();
            afficherCrises(toutesCrises);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Charge les types de crises dans le filtre
function chargerTypesCrises() {
    const select = document.getElementById('filter-type-crise');
    select.innerHTML = '<option value="">Tous les types</option>';
    typesCrisesDisponibles.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        select.appendChild(option);
    });
}

// Affiche les crises dans le tableau
function afficherCrises(crises) {
    const tbody = document.querySelector('#table-crises tbody');
    tbody.innerHTML = '';
    
    // Filtre par type si sélectionné
    const typeFiltre = document.getElementById('filter-type-crise').value;
    let crisesFiltrees = crises;
    if (typeFiltre) {
        crisesFiltrees = crises.filter(c => c.type_crise === typeFiltre);
    }
    
    if (crisesFiltrees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Aucune crise trouvée</td></tr>';
        return;
    }
    
    crisesFiltrees.forEach(crise => {
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
    
    const filterType = document.getElementById('filter-type-crise');
    if (filterType) {
        filterType.addEventListener('change', function() {
            afficherCrises(toutesCrises);
        });
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
        <div class="alert alert-warning alert-custom">
            <i class="fas fa-exclamation-triangle"></i> 
            <strong>Mécanique d'allocation :</strong> 25% des ressources sont réservées (non utilisées). 
            Les 75% restants sont alloués selon les besoins réels : si le stock est suffisant, chaque crise reçoit son besoin complet. 
            Sinon, toutes les allocations sont réduites proportionnellement par un coefficient unique.
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
        
        // Bloc avec toutes les crises actuelles traitées
        if (result.allocation && result.allocation.length > 0) {
            html += '<div class="card mt-3"><div class="card-header"><i class="fas fa-list"></i> Toutes les Crises Actuelles Traitées</div><div class="card-body">';
            html += '<div class="table-responsive"><table class="table table-hover table-striped" id="table-allocation">';
            html += '<thead><tr>';
            html += '<th>Rang</th><th>Nom de la Crise</th><th>Type</th><th>Pays</th><th>Intensité</th>';
            html += '<th>Score Urgence</th><th>Population</th><th>Accessibilité</th>';
            html += '</tr></thead><tbody>';
            
            result.allocation.forEach((crise, idx) => {
                const scoreUrgence = crise.score_urgence_normalise ? crise.score_urgence_normalise.toFixed(2) : 'N/A';
                const rowId = `crise-row-${idx}`;
                const detailRowId = `crise-detail-${idx}`;
                
                // Ligne principale (cliquable)
                html += `<tr class="crise-row" id="${rowId}" onclick="toggleCriseDetails(${idx})" style="cursor: pointer;">`;
                html += `<td><strong>${idx + 1}</strong></td>`;
                html += `<td><strong>${crise.nom_crise || 'N/A'}</strong> <i class="fas fa-chevron-down ms-1"></i></td>`;
                html += `<td><span class="badge bg-primary">${crise.type_crise || 'N/A'}</span></td>`;
                html += `<td>${crise.pays || 'N/A'}</td>`;
                html += `<td><span class="badge bg-danger">${crise.intensite || 'N/A'}</span></td>`;
                html += `<td>${scoreUrgence}%</td>`;
                html += `<td>${(crise.population_touchee || 0).toLocaleString('fr-FR')}</td>`;
                html += `<td>${(crise.accessibilite || 0).toFixed(2)}</td>`;
                html += '</tr>';
                
                // Ligne détaillée (cachée par défaut)
                html += `<tr id="${detailRowId}" class="crise-detail-row" style="display: none;">`;
                html += '<td colspan="8" class="bg-light">';
                html += '<div class="p-3">';
                html += '<h6 class="mb-3"><i class="fas fa-box-open"></i> Ressources Allouées</h6>';
                html += '<div class="row">';
                
                // Mapping des ressources avec leurs noms d'affichage
                const ressourcesMapping = {
                    'allocation_denrees_alimentaires_kg': 'Denrées alimentaires (kg)',
                    'allocation_eau_potable_litres': 'Eau potable (litres)',
                    'allocation_generateurs': 'Générateurs',
                    'allocation_hopitaux_campagne': 'Hôpitaux de campagne',
                    'allocation_medicaments_doses': 'Médicaments (doses)',
                    'allocation_personnel_medical': 'Personnel médical',
                    'allocation_tentes': 'Tentes',
                    'allocation_vehicules_urgence': 'Véhicules d urgence'
                };
                
                // Affiche les ressources allouées
                let hasAllocation = false;
                for (const [key, label] of Object.entries(ressourcesMapping)) {
                    const valeur = crise[key] || 0;
                    const ressourceKey = key.replace('allocation_', '');
                    const pourcentageKey = `pourcentage_satisfait_${ressourceKey}`;
                    const pourcentage = crise[pourcentageKey] || 0;
                    
                    if (valeur > 0) {
                        hasAllocation = true;
                    }
                    html += '<div class="col-md-6 mb-2">';
                    html += `<strong>${label}:</strong> <span class="badge ${valeur > 0 ? 'bg-success' : 'bg-secondary'}">${valeur.toLocaleString('fr-FR')}</span>`;
                    if (pourcentage > 0) {
                        html += ` <span class="badge bg-info">${pourcentage.toFixed(1)}% du besoin</span>`;
                    }
                    html += '</div>';
                }
                
                if (!hasAllocation) {
                    html += '<div class="col-12 mt-2"><em class="text-muted">Aucune ressource allouée pour cette crise.</em></div>';
                }
                
                html += '</div></div></td></tr>';
            });
            
            html += '</tbody></table></div>';
            html += '</div></div>';
        }
        
        // Affiche le stock réservé (25%)
        if (result.stock_reserve) {
            html += '<div class="card mt-3"><div class="card-header bg-warning"><i class="fas fa-lock"></i> Stocks Réservés (25% - Non Utilisés)</div><div class="card-body"><ul class="list-group">';
            
            for (const [ressource, quantite] of Object.entries(result.stock_reserve)) {
                html += `<li class="list-group-item">${ressource.replace(/_/g, ' ')}: <strong>${quantite.toLocaleString('fr-FR')}</strong></li>`;
            }
            
            html += '</ul></div></div>';
        }
        
        // Affiche les stocks restants (dans les 75% allouables)
        html += '<div class="card mt-3"><div class="card-header"><i class="fas fa-boxes"></i> Stocks Restants (dans les 75% Allouables)</div><div class="card-body"><ul class="list-group">';
        
        for (const [ressource, quantite] of Object.entries(result.stock_restant)) {
            html += `<li class="list-group-item">${ressource.replace(/_/g, ' ')}: ${quantite.toLocaleString('fr-FR')}</li>`;
        }
        
        html += '</ul></div></div>';
    }
    
    container.innerHTML = html;
}

// Fonction pour afficher/masquer les détails d'une crise
function toggleCriseDetails(idx) {
    const detailRow = document.getElementById(`crise-detail-${idx}`);
    const mainRow = document.getElementById(`crise-row-${idx}`);
    const icon = mainRow.querySelector('.fa-chevron-down, .fa-chevron-up');
    
    if (detailRow.style.display === 'none') {
        detailRow.style.display = '';
        if (icon) {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        }
        mainRow.classList.add('table-active');
    } else {
        detailRow.style.display = 'none';
        if (icon) {
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
        mainRow.classList.remove('table-active');
    }
}

// Génère la carte
async function genererCarte() {
    const includeAllocation = document.getElementById('include-allocation').checked;
    
    try {
        // La carte n'affiche que les crises actuelles
        const response = await fetch(`/api/carte?allocation=${includeAllocation}&actuelles=true`);
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

// Génère la carte avec heatmap de probabilité
async function genererCarteHeatmap() {
    const typeCrise = document.getElementById('heatmap-type-crise').value;
    const intensite = parseFloat(document.getElementById('heatmap-intensite').value);
    const resolution = parseFloat(document.getElementById('heatmap-resolution').value);
    
    if (!typeCrise) {
        alert('Veuillez sélectionner un type de crise');
        return;
    }
    
    if (isNaN(intensite) || intensite < 0 || intensite > 10) {
        alert('L\'intensité doit être entre 0 et 10');
        return;
    }
    
    if (isNaN(resolution) || resolution < 1 || resolution > 5) {
        alert('La résolution doit être entre 1 et 5 degrés');
        return;
    }
    
    const container = document.getElementById('carte-heatmap-container');
    container.innerHTML = `
        <div class="alert alert-info">
            <i class="fas fa-spinner fa-spin"></i> Calcul de la carte de probabilité en cours... 
            Cela peut prendre quelques instants selon la résolution choisie.
        </div>
    `;
    
    try {
        const response = await fetch(
            `/api/carte-heatmap?type_crise=${encodeURIComponent(typeCrise)}&intensite=${intensite}&resolution=${resolution}`
        );
        const result = await response.json();
        
        if (result.success) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> Carte de probabilité générée avec succès!
                    <a href="${result.url}" target="_blank" class="btn btn-danger btn-sm ms-2">
                        <i class="fas fa-external-link-alt"></i> Ouvrir la carte
                    </a>
                </div>
                <div class="alert alert-warning">
                    <i class="fas fa-info-circle"></i> 
                    <strong>Légende:</strong> 
                    <span style="color: #00ff00;">Vert clair</span> = Probabilité faible (0-20%), 
                    <span style="color: #ffff00;">Jaune</span> = Probabilité modérée (40-60%), 
                    <span style="color: #ff8000;">Orange</span> = Probabilité élevée (60-80%), 
                    <span style="color: #8b0000;">Rouge foncé</span> = Probabilité très élevée (80-100%)
                </div>
                <iframe src="${result.url}" width="100%" height="700" style="border: none; border-radius: 10px;"></iframe>
            `;
        } else {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> Erreur: ${result.error}
                </div>
            `;
        }
    } catch (error) {
        console.error('Erreur:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> Erreur lors de la génération: ${error.message}
            </div>
        `;
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
            // Affiche la population totale du pays et pré-remplit le champ population touchée
            document.getElementById('population-pays-info').textContent = paysData.population.toLocaleString('fr-FR');
            const populationInput = document.getElementById('population-touchee');
            if (!populationInput.value) {
                // Pré-remplit avec 10% de la population totale par défaut
                populationInput.value = Math.round(paysData.population * 0.1);
            }
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
    const populationTouchee = parseFloat(document.getElementById('population-touchee').value);
    const budget = parseFloat(document.getElementById('budget').value);
    
    if (!typeRisque) {
        alert('Veuillez sélectionner un type de risque');
        return;
    }
    
    if (!populationTouchee || populationTouchee <= 0) {
        alert('Veuillez entrer une population touchée valide');
        return;
    }
    
    if (populationTouchee > paysData.population) {
        alert('La population touchée ne peut pas être supérieure à la population totale du pays');
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
                population_touchee: populationTouchee,
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
            <div class="card-header bg-primary text-white">
                <i class="fas fa-users"></i> Informations sur la Population
            </div>
            <div class="card-body">
                <p><strong>Population totale du pays:</strong> ${result.pays.population.toLocaleString('fr-FR')} habitants</p>
                <p><strong>Population touchée par la crise:</strong> <span class="badge bg-danger">${(result.population_touchee || result.pays.population).toLocaleString('fr-FR')} habitants</span></p>
                <p><strong>Pourcentage de la population touchée:</strong> ${(((result.population_touchee || result.pays.population) / result.pays.population) * 100).toFixed(2)}%</p>
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


