import {apiClient} from "./apiClient";

// for some reason error handling in saga?
export const exportAPI = ({body}) => apiClient({url: '/export/', method: 'POST', body: body, errorHandling: false});
