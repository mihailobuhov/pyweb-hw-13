const url = 'http://localhost:8000/api/contacts/'

window.getContacts = async function (skip = 0, limit = 100) {
  const response = await fetch(`${url}?skip=${skip}&limit=${limit}`)
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  const contacts = await response.json()
  return contacts
}

window.createContact = async function (contact) {
  try {
    const response = await fetch(`${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(contact),
    })
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail[0].msg);
    }
  } catch (error) {
    throw error;
  }
}

window.editContact = async function (contact) {
  try {
    const response = await fetch(`${url}${contact.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(contact),
    })
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail[0].msg);
    }
  } catch (error) {
    throw error;
  }
}

window.deleteContact = async function (id) {
  const response = await fetch(`${url}${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
}

window.getUpcomingBirthdays = async function () {
  try {
    console.log(`Requesting birthdays without dates`);  // Логування
    const response = await fetch(`${url}birthdays`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const birthdays = await response.json();
    return birthdays;
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}

function getFormattedDate(date) {
  const year = date.getFullYear();
  const month = ('0' + (date.getMonth() + 1)).slice(-2);
  const day = ('0' + date.getDate()).slice(-2);
  return `${year}-${month}-${day}`;
}

document.addEventListener('DOMContentLoaded', async function() {
  try {
    const birthdays = await getUpcomingBirthdays();
    console.log('Birthdays:', birthdays);  // Вивід отриманих контактів
  } catch (error) {
    console.error('Error:', error);
  }
});
