class ChecklistApp {
    constructor() {
        this.container = document.getElementById('checklist-container');
        this.items = [];
        this.apiUrl = check42.apiUrl;
        this.sessionToken = localStorage.getItem('token');
        console.log(this.sessionToken)
        this.init();
    }

    init() {
        this.fetchItems();
    }

    fetchItems() {
        var context = {};
        context["httpMethod"] = "GET"
        $.ajax({
            method: 'GET',
            url: this.apiUrl + '/checks',
            //data: JSON.stringify(context),
            contentType: 'application/json',
            crossDomain: true, // Enable CORS support,
            headers: {
                'Authorization': this.sessionToken
            },
            success: (response) => {
                this.items = response.message;
                this.render();
            },
            error: (jqXHR, textStatus, errorThrown) => {
                console.error('Response: ', jqXHR.responseText);
                this.showError('Failed to load checklist items: ' + jqXHR.responseText);
            }
        });
    }

    render() {
        this.container.innerHTML = ''; // Clear previous content

        document.getElementById('save-frequency').addEventListener('click', () => {
            const frequency = document.getElementById('frequency-select').value;
            this.handleFrequencyChange(frequency);
        });

        const itemsContainer = document.createElement('div');
        itemsContainer.className = 'checklist-items';

        this.items.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = 'item';
            itemElement.innerHTML = `
                <div class="item-content">
                    <div class="item-title">${item.title}</div>
                    <div class="item-description">${item.description || 'No description available'}</div>
                </div>
                <div class="switch-container">
                    <label class="switch">
                        <input type="checkbox" id="toggle-${item.id}"
                            ${item.enabled ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                </div>
            `;
            itemElement.querySelector(`#toggle-${item.id}`).addEventListener('change', (e) => {
                this.handleToggle(item.id, e.target.checked);
            });

            itemsContainer.appendChild(itemElement);
        });

        this.container.appendChild(itemsContainer);
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="error">
                ${message}
            </div>
        `;
    }

    handleToggle(itemId, enabled) {
        // Get the toggle element
        const toggleElement = document.getElementById(`toggle-${itemId}`)
        if (!toggleElement) return;

        // Disable the toggle while processing
        toggleElement.disabled = true;
        const item = this.items.find(item => item.id === itemId);

        $.ajax({
            method: 'PUT',
            url: this.apiUrl + '/checks',
            contentType: 'application/json',
            data: JSON.stringify({
                checks: [{
                    id: itemId,
                    enabled: enabled
                }]
            }),
            crossDomain: true,
            headers: {
                'Accept': 'application/json',
                'Authorization': this.sessionToken
            },
            success: (response) => {
                console.log('Toggle success:', response);
                // Just update the local state, no need to re-render
                item.enabled = enabled;
                // Show success banner
                const banner = document.getElementById('success-banner');
                banner.style.display = 'block';
                banner.style.opacity = '1';

                // Hide banner after 3 seconds
                setTimeout(() => {
                    banner.style.opacity = '0';
                    setTimeout(() => {
                        banner.style.display = 'none';
                    }, 300); // Wait for fade out animation to complete
                }, 3000);
            },
            error: (jqXHR, textStatus, errorThrown) => {
                console.error('Toggle error:', {
                    status: jqXHR.status,
                    statusText: jqXHR.statusText,
                    responseText: jqXHR.responseText,
                    error: errorThrown
                });

                // Revert the toggle state on error
                toggleElement.checked = !enabled;
                alert('Failed to update check: ' + (jqXHR.responseText || errorThrown));
            },
            complete: () => {
                // Re-enable the toggle
                toggleElement.disabled = false;
            }
        });
    }

    handleFrequencyChange(newFrequency) {

        $.ajax({
            method: 'PUT',
            url: this.apiUrl + '/schedule',
            contentType: 'application/json',
            data: JSON.stringify({ frequency: newFrequency }),
            crossDomain: true,
            headers: {
                'Accept': 'application/json',
                'Authorization': this.sessionToken
            },
            success: (response) => {
                console.log('Schedule update success:', response);

                // Show success banner
                const banner = document.getElementById('success-banner');
                banner.style.display = 'block';
                banner.style.opacity = '1';

                setTimeout(() => {
                    banner.style.opacity = '0';
                    setTimeout(() => {
                        banner.style.display = 'none';
                    }, 300);
                }, 3000);
            },
            error: (jqXHR, textStatus, errorThrown) => {
                console.error('Schedule update error:', errorThrown);
                alert('Failed to update schedule: ' + (jqXHR.responseText || errorThrown));
            }
        });
    }

}

// Initialize the app when the page loads
$(document).ready(() => {
    new ChecklistApp();
});
