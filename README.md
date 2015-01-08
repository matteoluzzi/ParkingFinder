ParkFinder
==========

Progetto per il corso di SDCC

Dipendenze Front-end Server:
<ul>
  <li>tornado</li>
  <li>boto</li>
  <li>bcrypt<br>
    <code>wget "http://py-bcrypt.googlecode.com/files/py-bcrypt-0.2.tar.gz"</code><br>
    <code>tar -xzf py-bcrypt-0.2.tar.gz</code><br>
    <code>cd py-bcrypt-0.2</code><br>
    <code>python setup.py build</code><br>
    <code>sudo python setup.py install</code><br>
  
  </li>
</ul>
<p>
  Per l'avvio del server di front end bisogna lanciare il file <code>FrontEndServer.py</code> nella cartella FrontEndServer, specificando l'indirizzo della macchina nel file <code>settings/FrontEndServer.ini</code>
</p>
