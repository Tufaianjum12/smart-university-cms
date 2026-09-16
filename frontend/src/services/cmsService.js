import apiClient from "./apiClient";
export const cms = {
 organization: ()=>apiClient.get("/api/v1/organization"), settings: ()=>apiClient.get("/api/v1/organization/settings"), updateOrganization:(d)=>apiClient.patch("/api/v1/organization",d), updateSettings:(d)=>apiClient.put("/api/v1/organization/settings",d),
 list:(r)=>apiClient.get(`/api/v1/${r}`), create:(r,d)=>apiClient.post(`/api/v1/${r}`,d), update:(r,id,d)=>apiClient.patch(`/api/v1/${r}/${id}`,d), remove:(r,id)=>apiClient.delete(`/api/v1/${r}/${id}`),
 organizations:()=>apiClient.get("/api/v1/organizations"), createOrganization:(d)=>apiClient.post("/api/v1/organizations",d), updateOrganizationPlatform:(id,d)=>apiClient.patch(`/api/v1/organizations/${id}`,d), status:(id,a)=>apiClient.post(`/api/v1/organizations/${id}/${a}`)
};
