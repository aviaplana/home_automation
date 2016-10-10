#include "nodelist.h"

NodeList::NodeList() {
  node_list = NULL;
}

node_t* NodeList::searchNode(byte n_id) {
    if (this->isEmpty()) {
      return NULL;
    }
    
    node_t* current = node_list;
    
    while (current->next != NULL) {
      if (current->id == n_id) {
        return current;
      }
      
      current = current->next;
    }
    
    if (current->id == n_id) {
      return current;
    }
    
    return NULL;
}

byte NodeList::getPipe(byte n_id) {
    node_t* current = searchNode(n_id);
    return (current == NULL) ? NULL : current->pipe;
}

bool NodeList::addNode(byte n_id, byte n_pipe) {
  // If the id already exists, return false.
  if (this->searchNode(n_id) != NULL) {
    return false;
  }

  if (node_list == NULL) {
    node_list = malloc(sizeof(node_t));
    node_list->id = n_id;
    node_list->pipe = n_pipe;
    node_list->next = NULL;  
    return true;  
  }
  
  node_t* current = node_list;
  
  while (current->next != NULL) {
    current = current->next;
  }

  current->next = malloc(sizeof(node_t));
  current->next->id = n_id;
  current->next->pipe = n_pipe;
  current->next->next = NULL;    

  return true;
}


void NodeList::deleteNode(byte n_id) {
  if (this->isEmpty()) {
    return;
  }
  node_t* current = node_list;

  // First check if the node is in the first position
  if (current->id == n_id) {
    Serial.print("deleted");
    node_list = current->next;
    free(current);
    return;
  }

  while (current->next != NULL) {      
    if (current->next->id == n_id) {
      node_t* temp = current->next->next;
      free(current->next);
      current->next = temp;
      return;
    }
    
    current = current->next;
  }  
}

void NodeList::deleteAll() {
  if (this->isEmpty()) {
    return;
  }
  node_t* current = node_list;
  
  while (current->next != NULL) {
    node_t* temp = current;
    current = current->next;
    free(temp);      
  }

  free(current);
  node_list = NULL;
}



