if (window.clickerGameInitialized) {
    console.log("Clicker Game reeds geïnitialiseerd");
} else {
    window.clickerGameInitialized = true;
    console.log("Advanced Clicker Game v2.0 loaded!");

    function generateRequestId() {
        return Date.now() + '-' + Math.random().toString(36).substring(2, 10);
    }

    function sendJsonRpc(url, params) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params,
                id: Math.floor(Math.random() * 1000000)
            }),
            credentials: 'same-origin'
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error.message);
                return data.result;
            });
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return Math.floor(num).toString();
    }

    document.addEventListener('DOMContentLoaded', function () {
        // Elements
        const aapSelectie = document.getElementById('aap_selectie');
        const clickerGame = document.getElementById('clicker_game');
        const bananenAantal = document.getElementById('bananen_aantal');
        const banaanImg = document.getElementById('banaan_img');
        const messagesDiv = document.getElementById('messages');

        // Nieuwe elements voor upgrades
        let upgradeSection, botCountElement, bpsElement, multiplierElement;
        let buyBotButton, upgradeBotButton, upgradeMultiplierButton;
        let botCostElement, botUpgradeCostElement, multiplierCostElement;

        // State
        let currentAapId = null;
        let totalBananen = 0;
        let currentStats = {};
        let canClick = true;
        let isSubmitting = false;
        let updateInterval = null;
        let autoSaveInterval = null;
        let botBananenTeller = 0;

        function createUpgradeInterface() {
            upgradeSection = document.createElement('div');
            upgradeSection.id = 'upgrade_section';
            upgradeSection.className = 'mt-4';
            upgradeSection.innerHTML = `
                <div class="row">
                    <div class="col-md-12">
                        <h4>🤖 Game Upgrades</h4>
                        <div class="card">
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-4">
                                        <h5>📊 Stats</h5>
                                        <p><strong>Bots:</strong> <span id="bot_count">0</span></p>
                                        <p><strong>Productie:</strong> <span id="bananen_per_seconde">0 per min</span></p>
                                        <p><strong>Click Multiplier:</strong> x<span id="click_multiplier">1.0</span></p>
                                    </div>
                                    <div class="col-md-8">
                                        <h5>🛒 Shop</h5>
                                        <div class="upgrade-buttons">
                                            <button id="buy_bot" class="btn btn-primary mb-2">
                                                🤖 Koop Bot (<span id="bot_cost">10</span> 🍌)
                                            </button>
                                            <button id="upgrade_multiplier" class="btn btn-warning mb-2">
                                                ⚡ Upgrade Clicks (<span id="multiplier_cost">100</span> 🍌)
                                            </button>
                                            <button id="upgrade_bots" class="btn btn-success mb-2">
                                                🔧 Upgrade Bots (<span id="bot_upgrade_cost">250</span> 🍌)
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            clickerGame.appendChild(upgradeSection);

            // Bind elements
            botCountElement = document.getElementById('bot_count');
            bpsElement = document.getElementById('bananen_per_seconde');
            multiplierElement = document.getElementById('click_multiplier');
            buyBotButton = document.getElementById('buy_bot');
            upgradeBotButton = document.getElementById('upgrade_bots');
            upgradeMultiplierButton = document.getElementById('upgrade_multiplier');
            botCostElement = document.getElementById('bot_cost');
            botUpgradeCostElement = document.getElementById('bot_upgrade_cost');
            multiplierCostElement = document.getElementById('multiplier_cost');

            // Bind events
            buyBotButton.addEventListener('click', () => buyBot());
            upgradeMultiplierButton.addEventListener('click', () => upgradeMultiplier());
            upgradeBotButton.addEventListener('click', () => upgradeBots());
        }

        function updateStatsDisplay() {
            if (!currentStats.success) return;

            // Update bot aantal
            botCountElement.textContent = currentStats.aantal_bots || 0;

            // Toon bananen per minuut in plaats van per seconde voor betere UX
            const bps = currentStats.bananen_per_seconde || 0;
            const bpm = bps * 60; // Converteer naar bananen per minuut
            bpsElement.textContent = bpm.toFixed(1) + ' per min';

            // Update multiplier
            multiplierElement.textContent = (currentStats.click_multiplier || 1.0).toFixed(1);

            // Update kosten voor upgrades
            botCostElement.textContent = formatNumber(currentStats.bot_cost || 10);
            botUpgradeCostElement.textContent = formatNumber(currentStats.bot_upgrade_cost || 250);
            multiplierCostElement.textContent = formatNumber(currentStats.multiplier_cost || 100);

            // Update button states gebaseerd op beschikbare bananen
            const bananen = totalBananen;
            buyBotButton.disabled = bananen < (currentStats.bot_cost || 10);
            upgradeMultiplierButton.disabled = bananen < (currentStats.multiplier_cost || 100);
            upgradeBotButton.disabled = bananen < (currentStats.bot_upgrade_cost || 250);

            // Visueel effect voor knoppen
            buyBotButton.classList.toggle('affordable', bananen >= (currentStats.bot_cost || 10));
            upgradeMultiplierButton.classList.toggle('affordable', bananen >= (currentStats.multiplier_cost || 100));
            upgradeBotButton.classList.toggle('affordable', bananen >= (currentStats.bot_upgrade_cost || 250));
        }

        // Belangrijke nieuwe functie: haal server stats op en synchroniseer
        function syncWithServer() {
            if (currentAapId && !isSubmitting) {
                sendJsonRpc('/aaap/clicker/get-stats', {
                    aap_id: currentAapId
                }).then(function (result) {
                    if (result.success) {
                        currentStats = result;
                        totalBananen = result.bananen;
                        updateTotaalDisplay();
                        updateStatsDisplay();
                    }
                }).catch(function (error) {
                    console.error("Stats update error:", error);
                });
            }
        }

        // Initiële sync en start automatische updates
        function startSyncWithServer() {
            // Eerste sync direct
            syncWithServer();

            // Dan elke 5 seconden (niet te vaak om server te belasten)
            if (updateInterval) clearInterval(updateInterval);
            updateInterval = setInterval(syncWithServer, 5000);
        }

        // Visuele update van bananen teller
        function updateTotaalDisplay() {
            bananenAantal.textContent = formatNumber(totalBananen);
        }

        // Belangrijke functie: realtime bot productie
        function startBotProduction() {
            let lastUpdate = Date.now();

            if (autoSaveInterval) clearInterval(autoSaveInterval);

            autoSaveInterval = setInterval(() => {
                if (!currentAapId || !currentStats.bananen_per_seconde) return;

                const now = Date.now();
                const seconds = (now - lastUpdate) / 1000;
                lastUpdate = now;

                // Bereken bot productie
                const productie = currentStats.bananen_per_seconde * seconds;
                botBananenTeller += productie;

                // Als er minstens 1 banaan is geproduceerd
                if (botBananenTeller >= 1) {
                    const aantalNieuw = Math.floor(botBananenTeller);
                    botBananenTeller -= aantalNieuw;

                    // Update lokale teller
                    totalBananen += aantalNieuw;
                    updateTotaalDisplay();
                    updateStatsDisplay();

                    // Visuele feedback
                    if (Math.random() < 0.3) {
                        banaanImg.classList.add('bot-working');
                        setTimeout(() => {
                            banaanImg.classList.remove('bot-working');
                        }, 200);
                    }

                    // Toon bericht bij grote aantallen
                    if (aantalNieuw >= 5) {
                        showMessage('info', `🤖 Bots verzamelden ${aantalNieuw} bananen!`);
                    }
                }
            }, 100); // Update 10x per seconde voor vloeiende animatie
        }

        function buyBot() {
            if (isSubmitting) return;
            isSubmitting = true;
            buyBotButton.disabled = true;

            sendJsonRpc('/aaap/clicker/buy-bot', {
                aap_id: currentAapId
            }).then(function (result) {
                isSubmitting = false;

                if (result.success) {
                    showMessage('success', `🤖 Bot gekocht! Je hebt nu ${result.aantal_bots} bots.`);

                    // Update direct
                    totalBananen = result.nieuwe_bananen;
                    updateTotaalDisplay();

                    // Update stats
                    currentStats.bananen = result.nieuwe_bananen;
                    currentStats.aantal_bots = result.aantal_bots;
                    currentStats.bot_cost = result.nieuwe_bot_cost;
                    currentStats.bananen_per_seconde = result.bananen_per_seconde;
                    updateStatsDisplay();
                } else {
                    showMessage('danger', result.error);
                    buyBotButton.disabled = false;
                }
            }).catch(function (error) {
                isSubmitting = false;
                buyBotButton.disabled = false;
                showMessage('danger', 'Fout bij kopen bot');
            });
        }

        function upgradeMultiplier() {
            if (isSubmitting) return;
            isSubmitting = true;
            upgradeMultiplierButton.disabled = true;

            sendJsonRpc('/aaap/clicker/upgrade-multiplier', {
                aap_id: currentAapId
            }).then(function (result) {
                isSubmitting = false;

                if (result.success) {
                    showMessage('success', `⚡ Click multiplier upgraded naar x${result.click_multiplier.toFixed(1)}!`);

                    // Update direct
                    totalBananen = result.nieuwe_bananen;
                    updateTotaalDisplay();

                    // Update stats
                    currentStats.bananen = result.nieuwe_bananen;
                    currentStats.click_multiplier = result.click_multiplier;
                    currentStats.multiplier_level = result.multiplier_level;
                    currentStats.multiplier_cost = result.nieuwe_upgrade_cost;
                    updateStatsDisplay();
                } else {
                    showMessage('danger', result.error);
                    upgradeMultiplierButton.disabled = false;
                }
            }).catch(function (error) {
                isSubmitting = false;
                upgradeMultiplierButton.disabled = false;
                showMessage('danger', 'Fout bij upgraden multiplier');
            });
        }

        function upgradeBots() {
            if (isSubmitting) return;
            isSubmitting = true;
            upgradeBotButton.disabled = true;

            sendJsonRpc('/aaap/clicker/upgrade-bots', {
                aap_id: currentAapId
            }).then(function (result) {
                isSubmitting = false;

                if (result.success) {
                    showMessage('success', `🔧 Bots upgraded naar level ${result.bot_level}!`);

                    // Update direct
                    totalBananen = result.nieuwe_bananen;
                    updateTotaalDisplay();

                    // Update stats
                    currentStats.bananen = result.nieuwe_bananen;
                    currentStats.bot_level = result.bot_level;
                    currentStats.bananen_per_seconde = result.bananen_per_seconde;
                    currentStats.bot_upgrade_cost = result.nieuwe_upgrade_cost;
                    updateStatsDisplay();
                } else {
                    showMessage('danger', result.error);
                    upgradeBotButton.disabled = false;
                }
            }).catch(function (error) {
                isSubmitting = false;
                upgradeBotButton.disabled = false;
                showMessage('danger', 'Fout bij upgraden bots');
            });
        }

        function showMessage(type, message) {
            messagesDiv.className = `alert alert-${type} mt-3`;
            messagesDiv.textContent = message;
            messagesDiv.style.display = 'block';

            setTimeout(() => {
                messagesDiv.style.display = 'none';
            }, 3000);
        }

        // Nieuwe functie: direct opslaan van bananen
        function clickBanaan() {
            if (isSubmitting || !canClick) return;

            canClick = false;
            setTimeout(() => { canClick = true; }, 300); // Voorkom spam clicks

            // Animatie
            banaanImg.classList.add('clicked');
            setTimeout(() => banaanImg.classList.remove('clicked'), 100);

            const multiplier = currentStats.click_multiplier || 1.0;
            const clickValue = Math.floor(multiplier);

            // Direct lokaal updaten voor responsiveness
            totalBananen += clickValue;
            updateTotaalDisplay();
            updateStatsDisplay();

            // Stuur direct naar server
            const requestId = generateRequestId();
            isSubmitting = true;

            sendJsonRpc('/aaap/clicker/update', {
                aap_id: currentAapId,
                bananen: 1, // Altijd 1 banaan per klik (multiplier wordt server-side toegepast)
                request_id: requestId
            }).then(function (result) {
                isSubmitting = false;

                if (result.success) {
                    // Synchroniseer met server-waarde om drift te voorkomen
                    totalBananen = result.nieuwe_waarde;
                    updateTotaalDisplay();

                    // Toon feedback alleen bij meerdere bananen
                    if (result.bananen_toegevoegd > 1) {
                        const feedback = document.createElement('div');
                        feedback.className = 'banaan-feedback';
                        feedback.textContent = `+${result.bananen_toegevoegd}`;
                        feedback.style.left = `${Math.random() * 50 + 25}%`;
                        clickerGame.appendChild(feedback);

                        setTimeout(() => {
                            feedback.classList.add('fade-out');
                            setTimeout(() => feedback.remove(), 1000);
                        }, 100);
                    }
                } else {
                    showMessage('danger', result.error);
                }
            }).catch(function (error) {
                isSubmitting = false;
                showMessage('danger', 'Fout bij opslaan bananen');
            });
        }

        // Event listeners
        aapSelectie.addEventListener('change', function () {
            currentAapId = this.value;
            if (currentAapId) {
                const selectedOption = this.options[this.selectedIndex];
                totalBananen = parseInt(selectedOption.dataset.bananen || 0);
                updateTotaalDisplay();
                clickerGame.style.display = 'block';
                messagesDiv.style.display = 'none';

                if (!upgradeSection) {
                    createUpgradeInterface();
                }

                // Start automatische updates
                startSyncWithServer();
                startBotProduction();

            } else {
                clickerGame.style.display = 'none';
                if (updateInterval) {
                    clearInterval(updateInterval);
                    updateInterval = null;
                }
                if (autoSaveInterval) {
                    clearInterval(autoSaveInterval);
                    autoSaveInterval = null;
                }
            }
        });

        // Direct klikken op banaan zonder aparte opslaan knop
        banaanImg.addEventListener('click', clickBanaan);

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            #banaan_img {
                transition: transform 0.1s;
                cursor: pointer;
            }
            #banaan_img.clicked {
                transform: scale(1.1);
            }
            #banaan_img.bot-working {
                transform: scale(1.03);
                opacity: 0.9;
            }
            #banaan_img {
                user-select: none;
                -webkit-user-select: none;
            }
            .upgrade-buttons button:disabled {
                cursor: not-allowed;
                opacity: 0.7;
            }
            .upgrade-buttons button {
                display: block;
                width: 100%;
                margin-bottom: 10px;
            }
            .card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
            }
            .upgrade-buttons button:not(:disabled):hover {
                transform: scale(1.02);
                transition: transform 0.2s;
            }
            .upgrade-buttons button.affordable {
                box-shadow: 0 0 8px #ffcc00;
                transform: scale(1.02);
            }
            .upgrade-buttons button.affordable:hover {
                transform: scale(1.04);
            }
            .banaan-feedback {
                position: absolute;
                color: #ffcc00;
                font-weight: bold;
                font-size: 24px;
                animation: float-up 1.5s ease-out;
                text-shadow: 0px 0px 3px #000;
                pointer-events: none;
            }
            @keyframes float-up {
                0% { transform: translateY(0); opacity: 1; }
                100% { transform: translateY(-50px); opacity: 0; }
            }
            .fade-out {
                opacity: 0;
                transition: opacity 1s;
            }
        `;
        document.head.appendChild(style);
    });
}