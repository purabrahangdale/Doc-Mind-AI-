import api from './api';

/**
 * Sends a user question to the RAG chat backend service.
 * @param {string} question - The user query to ask.
 * @returns {Promise<object>} The JSON response containing question, answer, and sources list.
 */
export const sendMessage = async (question, documentId = null) => {
  try {
    const payload = { question };
    if (documentId) {
      payload.document_id = documentId;
    }
    const response = await api.post('/chat', payload);
    return response.data;
  } catch (error) {
    console.error('Error in sendMessage API call:', error);
    throw error;
  }
};
