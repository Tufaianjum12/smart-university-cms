import apiClient from './apiClient';
const base='/api/v1';
export const courseApi={
 courses:()=>apiClient.get(`${base}/courses`), createCourse:d=>apiClient.post(`${base}/courses`,d), updateCourse:(id,d)=>apiClient.patch(`${base}/courses/${id}`,d), archiveCourse:id=>apiClient.delete(`${base}/courses/${id}`),
 prerequisites:id=>apiClient.get(`${base}/courses/${id}/prerequisites`), addPrerequisite:(id,d)=>apiClient.post(`${base}/courses/${id}/prerequisites`,d), removePrerequisite:id=>apiClient.delete(`${base}/prerequisites/${id}`),
 curriculum:id=>apiClient.get(`${base}/programs/${id}/curriculum`), addCurriculum:(id,d)=>apiClient.post(`${base}/programs/${id}/curriculum`,d), removeCurriculum:id=>apiClient.delete(`${base}/curriculum/${id}`),
 offerings:()=>apiClient.get(`${base}/course-offerings`), createOffering:d=>apiClient.post(`${base}/course-offerings`,d), updateOffering:(id,d)=>apiClient.patch(`${base}/course-offerings/${id}`,d), archiveOffering:id=>apiClient.delete(`${base}/course-offerings/${id}`),
 enrollments:(params={})=>apiClient.get(`${base}/enrollments`,{params}), enroll:d=>apiClient.post(`${base}/enrollments`,d), updateEnrollment:(id,d)=>apiClient.patch(`${base}/enrollments/${id}`,d)
};
